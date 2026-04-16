import reflex as rx

class ReactRnd(rx.Component):
    """Reflex wrapper for react-rnd (Resizable and Draggable component)."""
    
    library = "react-rnd"
    tag = "Rnd"

    # Properties
    default: rx.Var[dict]
    position: rx.Var[dict]
    size: rx.Var[dict]
    
    min_width: rx.Var[int] | rx.Var[str]
    min_height: rx.Var[int] | rx.Var[str]
    max_width: rx.Var[int] | rx.Var[str]
    max_height: rx.Var[int] | rx.Var[str]
    
    bounds: rx.Var[str]
    drag_handle_class_name: rx.Var[str]
    
    # Disable dragging on specific elements (like inputs)
    cancel: rx.Var[str]

    def get_event_triggers(self) -> dict[str, rx.Var | type[rx.Var]]:
        return {
            **super().get_event_triggers(),
            "on_drag_stop": lambda e, d: [d],
            "on_resize_stop": lambda e, dir, ref, delta, position: [ref, position],
        }

rnd = ReactRnd.create
