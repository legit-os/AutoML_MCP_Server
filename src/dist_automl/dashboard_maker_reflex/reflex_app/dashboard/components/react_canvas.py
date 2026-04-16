import reflex as rx

class TransformWrapperBase(rx.Component):
    library = "react-zoom-pan-pinch"
    tag = "TransformWrapper"
    
    min_scale: rx.Var[float]
    max_scale: rx.Var[float]
    initial_scale: rx.Var[float]
    initial_position_x: rx.Var[float]
    initial_position_y: rx.Var[float]
    
    panning: rx.Var[dict]   # e.g. {"disabled": False, "excluded": ["class1"]}
    wheel: rx.Var[dict]     # e.g. {"step": 0.1}
    pinch: rx.Var[dict]
    double_click: rx.Var[dict]
    limit_to_bounds: rx.Var[bool]


class TransformComponentBase(rx.Component):
    library = "react-zoom-pan-pinch"
    tag = "TransformComponent"
    
    wrapper_style: rx.Var[dict]
    content_style: rx.Var[dict]


transform_wrapper = TransformWrapperBase.create
transform_component = TransformComponentBase.create
