import plotly.graph_objects as go


def generate_rack_layout(map_config, save_path):

    racks = map_config["racks"]
    map_height = map_config["map_height"]
    map_width = map_config["map_width"]

    # Define the color map based on pick_direction
    color_map = {
        "vertical": "lightgreen",
        "horizontal": "lightcoral"
    }

    # Create figure
    fig = go.Figure()

    # Add rectangles for each rack
    for rack in racks:
        fig.add_shape(
            type="rect",
            x0=rack['pos'][1],
            y0=rack['pos'][0],
            x1=rack['pos'][1] + rack['width'],
            y1=rack['pos'][0] + rack['height'],
            line=dict(color="RoyalBlue"),
            #fillcolor=color_map[rack['pick_direction']],
            fillcolor="lightgreen",
            opacity=0.6,
        )
        # Add scatter trace for hover data
        fig.add_trace(
            go.Scatter(
                x=[rack['pos'][1] + rack['width']/2],
                y=[rack['pos'][0] + rack['height']/2],
                text=f"Rack ID: {rack['rack_id']} <br>Position: ({rack['pos'][1]}, {rack['pos'][0]})<br>Size: {rack['width']}x{rack['height']}",
                mode="markers",
                marker=dict(size=2, color="rgba(0,0,0,0)"),
                hoverinfo="text",
                showlegend=False  # Add this line to hide the trace numbers
            )
        )

    # Set axes properties and reverse y-axis
    fig.update_xaxes(range=[0, map_width], dtick=5)
    fig.update_yaxes(range=[map_height, 0], dtick=5)  # Reversed y-axis

    # Add grid and title
    fig.update_layout(
        title="倉庫レイアウト",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        height=600,
        width=600,
        showlegend=False  # Add this line to hide the legend
    )

    # Show figure
    fig.show()

    # Save the figure as an HTML file
    fig.write_html(save_path / "rack_layout.html")