"""AutoML Dashboard — powered by Reflex.

A grid-based dashboard where users can select captured Python variables
(DataFrames, matplotlib figures, lists, dicts, KPIs) from a sidebar and
view them as interactive widget cards on a responsive grid.
"""

import json
from pathlib import Path

import reflex as rx
from pydantic import BaseModel
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse

from .components.react_rnd import rnd
from .components.react_canvas import transform_wrapper, transform_component


# ---------------------------------------------------------------------------
# Project root discovery
# ---------------------------------------------------------------------------

_PROJECT_FILE = (
    Path(__file__).parent.parent.parent.parent / "managers" / "current_project_root.txt"
)


def _get_project_root() -> str:
    """Return the current project root directory or empty string."""
    if _PROJECT_FILE.exists():
        return _PROJECT_FILE.read_text().strip()
    return ""


# ---------------------------------------------------------------------------
# Reflex Models
# ---------------------------------------------------------------------------


class VariableInfo(BaseModel):
    """Flat representation of a variable from metadata.json."""

    key: str  # "script_path::var_name"
    name: str
    script_key: str
    var_type: str
    rel_path: str


class WidgetItem(BaseModel):
    """All data needed to render one dashboard widget."""

    id: str
    name: str
    script_key: str
    var_type: str
    rel_path: str
    # Type-specific payloads
    df_columns: list[str] = []
    df_rows: list[list[str]] = []
    list_data: list[str] = []
    dict_data: str = ""
    kpi_value: str = ""
    image_url: str = ""
    # Canvas Layout
    x: float = 50
    y: float = 50
    width: float = 400
    height: float = 300


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class DashboardState(rx.State):
    """Manages the dashboard state: metadata, selection, and widget data."""

    scripts_metadata: dict[str, dict[str, dict[str, str]]] = {}
    active_widgets: list[WidgetItem] = []
    selected_keys: list[str] = []
    _project_root: str = ""

    def on_load(self):
        """Load metadata from disk on page load."""
        self._project_root = _get_project_root()
        if not self._project_root:
            return
        meta_file = Path(self._project_root) / "dashboard_runs" / "metadata.json"
        if meta_file.exists():
            with open(meta_file) as f:
                data = json.load(f)
            self.scripts_metadata = data.get("scripts", {})

    def refresh(self):
        """Reload metadata, clearing all current widgets."""
        self.selected_keys = []
        self.active_widgets = []
        self.on_load()

    # -- Computed vars -------------------------------------------------------

    @rx.var
    def variable_list(self) -> list[VariableInfo]:
        """Flat list of all available variables across all scripts."""
        result: list[VariableInfo] = []
        for script_key, variables in self.scripts_metadata.items():
            for name, info in variables.items():
                result.append(
                    VariableInfo(
                        key=f"{script_key}::{name}",
                        name=name,
                        script_key=script_key,
                        var_type=info.get("type", ""),
                        rel_path=info.get("path", ""),
                    )
                )
        return result

    @rx.var
    def has_variables(self) -> bool:
        return len(self.scripts_metadata) > 0

    @rx.var
    def has_widgets(self) -> bool:
        return len(self.active_widgets) > 0

    # -- Event handlers ------------------------------------------------------

    def toggle_variable(self, key: str):
        """Add or remove a widget for the given variable key."""
        # Deselect
        if key in self.selected_keys:
            self.selected_keys = [k for k in self.selected_keys if k != key]
            self.active_widgets = [
                w for w in self.active_widgets if w.id != key
            ]
            return

        # Select — build widget data
        script_key, name = key.split("::", 1)
        var_info = self.scripts_metadata.get(script_key, {}).get(name, {})
        var_type = var_info.get("type", "")
        rel_path = var_info.get("path", "")

        widget = WidgetItem(
            id=key,
            name=name,
            script_key=script_key,
            var_type=var_type,
            rel_path=rel_path,
            x=float(var_info.get("x", 50)),
            y=float(var_info.get("y", 50)),
            width=float(var_info.get("width", 400)),
            height=float(var_info.get("height", 300)),
        )

        base = Path(self._project_root) / "dashboard_runs"
        full_path = base / rel_path

        if var_type == "figure" and full_path.exists():
            api_url = rx.config.get_config().api_url
            widget.image_url = f"{api_url}/api/dashboard-image?path={rel_path}"
        elif full_path.exists():
            try:
                raw = json.loads(full_path.read_text())
            except Exception:
                raw = {}

            if var_type == "dataframe":
                cols = raw.get("columns", [])
                rows = raw.get("rows", [])
                widget.df_columns = cols
                widget.df_rows = [
                    [str(r.get(c, "")) for c in cols] for r in rows
                ]
            elif var_type == "list":
                widget.list_data = [str(v) for v in raw]
            elif var_type == "dict":
                widget.dict_data = json.dumps(raw, indent=2)
            elif var_type == "kpi":
                widget.kpi_value = str(raw.get("value", ""))

        self.selected_keys = [*self.selected_keys, key]
        self.active_widgets = [*self.active_widgets, widget]

    def update_layout(self, id: str, layout_data: dict):
        """Update widget layout properties and save to metadata.json."""
        script_key, name = id.split("::", 1)
        
        # 1. Update in-memory state securely for reactivity
        updated_widgets = []
        for w in self.active_widgets:
            if w.id == id:
                w.x = layout_data.get("x", w.x)
                w.y = layout_data.get("y", w.y)
                w.width = layout_data.get("width", w.width)
                w.height = layout_data.get("height", w.height)
            updated_widgets.append(w)
        self.active_widgets = updated_widgets

        # 2. Update memory metadata dictionary cleanly
        new_meta = self.scripts_metadata.copy()
        if script_key in new_meta and name in new_meta[script_key]:
            script_meta = new_meta[script_key].copy()
            var_meta = script_meta[name].copy()
            
            var_meta["x"] = layout_data.get("x", var_meta.get("x"))
            var_meta["y"] = layout_data.get("y", var_meta.get("y"))
            var_meta["width"] = layout_data.get("width", var_meta.get("width"))
            var_meta["height"] = layout_data.get("height", var_meta.get("height"))
            
            script_meta[name] = var_meta
            new_meta[script_key] = script_meta
        self.scripts_metadata = new_meta

        # 3. Flush to disk safely without Reflex Proxies
        meta_file = Path(self._project_root) / "dashboard_runs" / "metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r") as f:
                    data = json.load(f)
                
                if script_key in data.get("scripts", {}) and name in data["scripts"][script_key]:
                    element = data["scripts"][script_key][name]
                    if "x" in layout_data: element["x"] = float(layout_data["x"])
                    if "y" in layout_data: element["y"] = float(layout_data["y"])
                    if "width" in layout_data: element["width"] = float(layout_data["width"])
                    if "height" in layout_data: element["height"] = float(layout_data["height"])
                
                with open(meta_file, "w") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Error saving layout: {e}")

    def on_drag_stop(self, id: str, data: dict):
        self.update_layout(id, {"x": float(data.get("x", 0)), "y": float(data.get("y", 0))})

    def on_resize_stop(self, id: str, ref: dict, position: dict):
        try:
            # ref.style.width comes through as a string like "400px" in the JSON dict
            width_str = ref.get("style", {}).get("width", "")
            height_str = ref.get("style", {}).get("height", "")
            
            width = float(str(width_str).replace("px", "")) if width_str else None
            height = float(str(height_str).replace("px", "")) if height_str else None
            
            layout_update = {
                "x": float(position.get("x", 0)),
                "y": float(position.get("y", 0)),
            }
            if width is not None: layout_update["width"] = width
            if height is not None: layout_update["height"] = height
            
            self.update_layout(id, layout_update)
        except Exception as e:
            print(f"Resize dict parsing error: {e}")



# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------


def type_badge(var_type) -> rx.Component:
    """Colored badge indicating the variable type."""
    return rx.badge(
        var_type,
        color_scheme=rx.match(
            var_type,
            ("dataframe", "blue"),
            ("figure", "purple"),
            ("list", "green"),
            ("dict", "orange"),
            ("kpi", "red"),
            "gray",
        ),
        variant="soft",
        size="1",
    )


def variable_item(info: VariableInfo) -> rx.Component:
    """A single clickable row in the sidebar variable list."""
    is_selected = DashboardState.selected_keys.contains(info.key)

    return rx.flex(
        # Toggle icon
        rx.cond(
            is_selected,
            rx.icon("square-check", size=16, color="var(--accent-9)"),
            rx.icon("square", size=16, color="var(--gray-8)"),
        ),
        # Variable name
        rx.text(
            info.name,
            size="2",
            weight=rx.cond(is_selected, "medium", "regular"),
            color=rx.cond(is_selected, "var(--accent-11)", "var(--gray-12)"),
        ),
        # Spacer
        rx.spacer(),
        # Type badge
        type_badge(info.var_type),
        # Layout
        align="center",
        spacing="3",
        padding_x="12px",
        padding_y="8px",
        border_radius="8px",
        background=rx.cond(is_selected, "var(--accent-a3)", "transparent"),
        _hover={"background": "var(--gray-a3)"},
        cursor="pointer",
        transition="background 0.15s ease",
        on_click=lambda: DashboardState.toggle_variable(info.key),
        width="100%",
    )


def sidebar() -> rx.Component:
    """Left sidebar with variable browser and refresh button."""
    return rx.box(
        rx.vstack(
            # ---- Header ----
            rx.flex(
                rx.hstack(
                    rx.icon(
                        "layout-dashboard",
                        size=22,
                        color="var(--accent-9)",
                    ),
                    rx.heading("Dashboard", size="5", weight="bold"),
                    align="center",
                    spacing="2",
                ),
                rx.icon_button(
                    rx.icon("refresh-cw", size=16),
                    on_click=DashboardState.refresh,
                    variant="ghost",
                    size="2",
                    cursor="pointer",
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.separator(),
            # ---- Variables section ----
            rx.text(
                "VARIABLES",
                size="1",
                color="var(--gray-9)",
                weight="bold",
                letter_spacing="0.1em",
            ),
            rx.cond(
                DashboardState.has_variables,
                rx.vstack(
                    rx.foreach(DashboardState.variable_list, variable_item),
                    spacing="1",
                    width="100%",
                ),
                rx.box(
                    rx.callout(
                        "No variables found. Run an analysis script first.",
                        icon="info",
                        color_scheme="blue",
                        size="1",
                    ),
                    padding_top="8px",
                ),
            ),
            spacing="4",
            padding="20px",
            height="100%",
        ),
        width="300px",
        min_width="300px",
        height="100vh",
        border_right="1px solid var(--gray-a4)",
        background="var(--color-panel-solid)",
        overflow_y="auto",
    )


# -- Widget renderers --------------------------------------------------------


def render_dataframe_widget(widget: WidgetItem) -> rx.Component:
    return rx.box(
        rx.data_table(
            data=widget.df_rows,
            columns=widget.df_columns,
            pagination=True,
            search=True,
            sort=True,
        ),
        width="100%",
        overflow="auto",
    )


def render_figure_widget(widget: WidgetItem) -> rx.Component:
    return rx.image(
        src=widget.image_url,
        width="100%",
        border_radius="8px",
    )


def render_list_widget(widget: WidgetItem) -> rx.Component:
    return rx.vstack(
        rx.foreach(
            widget.list_data,
            lambda item: rx.flex(
                rx.box(
                    width="6px",
                    height="6px",
                    border_radius="50%",
                    background="var(--accent-9)",
                    flex_shrink="0",
                    margin_top="7px",
                ),
                rx.text(item, size="2"),
                spacing="2",
                align="start",
            ),
        ),
        spacing="2",
        width="100%",
    )


def render_dict_widget(widget: WidgetItem) -> rx.Component:
    return rx.code_block(
        widget.dict_data,
        language="json",
        show_line_numbers=True,
        wrap_long_lines=True,
    )


def render_kpi_widget(widget: WidgetItem) -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading(
                widget.kpi_value,
                size="8",
                weight="bold",
                color="var(--accent-11)",
            ),
            rx.text(widget.name, size="2", color="var(--gray-9)"),
            align="center",
            spacing="1",
        ),
        padding="24px",
        width="100%",
    )


def widget_content(widget: WidgetItem) -> rx.Component:
    """Route to the correct renderer based on variable type."""
    return rx.match(
        widget.var_type,
        ("dataframe", render_dataframe_widget(widget)),
        ("figure", render_figure_widget(widget)),
        ("list", render_list_widget(widget)),
        ("dict", render_dict_widget(widget)),
        ("kpi", render_kpi_widget(widget)),
        rx.text("Unsupported variable type", size="2", color="var(--red-9)"),
    )


def widget_card(widget: WidgetItem) -> rx.Component:
    """One card on the dashboard canvas."""
    card_content = rx.card(
        rx.vstack(
            # Card header (Acts as the drag handle)
            rx.flex(
                rx.text(widget.name, size="3", weight="bold"),
                rx.spacer(),
                type_badge(widget.var_type),
                align="center",
                width="100%",
                class_name="drag-handle",
                cursor="move",
                padding_bottom="1",
                border_bottom="1px solid var(--gray-a4)",
            ),
            # Card body
            rx.box(
                widget_content(widget),
                width="100%",
                height="100%",
                overflow="auto",
            ),
            spacing="3",
            width="100%",
            height="100%",
        ),
        width="100%",
        height="100%",
        variant="surface",
        style={"overflow": "hidden"}
    )
    
    return rnd(
        card_content,
        default={
            "x": widget.x,
            "y": widget.y,
            "width": widget.width,
            "height": widget.height,
        },
        bounds="parent",
        drag_handle_class_name="drag-handle",
        on_drag_stop=lambda d: DashboardState.on_drag_stop(widget.id, d),
        on_resize_stop=lambda ref, position: DashboardState.on_resize_stop(widget.id, ref, position),
        style={"position": "absolute", "zIndex": "10"}
    )


# -- Main area ---------------------------------------------------------------


def empty_canvas() -> rx.Component:
    """Placeholder shown when no widgets are active."""
    return rx.center(
        rx.vstack(
            rx.icon(
                "layout-dashboard",
                size=72,
                stroke_width=1,
                color="var(--gray-6)",
            ),
            rx.heading(
                "Your Dashboard",
                size="6",
                color="var(--gray-8)",
            ),
            rx.text(
                "Select variables from the sidebar to add widgets",
                size="3",
                color="var(--gray-7)",
            ),
            align="center",
            spacing="4",
        ),
        height="100%",
        width="100%",
    )


def main_canvas() -> rx.Component:
    """Main area: Infinite pannable canvas containing absolutely positioned widgets."""
    
    canvas_container = rx.cond(
        DashboardState.has_widgets,
        rx.box(
            rx.foreach(DashboardState.active_widgets, widget_card),
            width="5000px",  # Large virtual chart paper
            height="5000px",
            position="relative",
            background_image="radial-gradient(var(--gray-a4) 1px, transparent 1px)",
            background_size="25px 25px",
        ),
        empty_canvas(),
    )
    
    return rx.box(
        transform_wrapper(
            transform_component(
                canvas_container,
                wrapper_style={"width": "100%", "height": "100%"},
            ),
            initial_scale=1,
            min_scale=0.1,
            max_scale=3,
            panning={"disabled": False, "excluded": ["drag-handle"]},
            wheel={"step": 0.05},
        ),
        flex="1",
        width="100%",
        height="100vh",
        background="var(--gray-1)",
        overflow="hidden",
    )


# -- Page layout -------------------------------------------------------------


def index() -> rx.Component:
    """Root page layout: sidebar + main canvas."""
    return rx.flex(
        sidebar(),
        main_canvas(),
        direction="row",
        width="100%",
        height="100vh",
    )


# ---------------------------------------------------------------------------
# App & API
# ---------------------------------------------------------------------------

# Custom FastAPI app for serving dashboard images
custom_api = FastAPI()


@custom_api.get("/api/dashboard-image")
async def _serve_dashboard_image(path: str = Query(...)):
    """Serve a captured matplotlib figure PNG from dashboard_runs."""
    project_root = _get_project_root()
    if not project_root:
        return JSONResponse({"error": "no project set"}, status_code=404)
    full = Path(project_root) / "dashboard_runs" / path
    if full.exists() and full.suffix == ".png":
        return FileResponse(str(full), media_type="image/png")
    return JSONResponse({"error": "file not found"}, status_code=404)


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="blue",
        radius="medium",
        scaling="100%",
    ),
    style={
        "::selection": {"background": "var(--accent-5)"},
    },
    api_transformer=custom_api,
)

app.add_page(index, title="AutoML Dashboard", on_load=DashboardState.on_load)
