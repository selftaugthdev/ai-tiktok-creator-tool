import io

import plotly.graph_objects as go
from PIL import Image

CHART_W = 920
CHART_H = 520


def generate_chart_image(chart_data: dict) -> Image.Image:
    """Render chart_data as a PIL Image using Plotly."""
    fig = go.Figure(
        go.Bar(
            x=chart_data["labels"],
            y=chart_data["values"],
            marker_color="#FF6B9D",
            marker_line_width=0,
        )
    )
    fig.update_layout(
        title=dict(
            text=chart_data.get("title", ""),
            font=dict(size=28, color="#2D2D2D"),
            x=0.5,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2D2D2D", size=20),
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=18)),
        yaxis=dict(showgrid=False, showline=False, visible=False),
        bargap=0.3,
    )
    img_bytes = fig.to_image(format="png", width=CHART_W, height=CHART_H, scale=1)
    return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
