import math
import random
import json

def create_muller_lyer_figure(x, y, line_length, arrow_length, angle, line_thickness, direction='out'):
    """
    Generate SVG elements for a single Müller-Lyer figure.
    
    :param x: X-coordinate of the center of the line
    :param y: Y-coordinate of the center of the line
    :param line_length: Length of the main line
    :param arrow_length: Length of the arrow lines
    :param angle: Angle of the arrow lines in degrees
    :param line_thickness: Thickness of the lines
    :param direction: 'out' for outward arrows, 'in' for inward arrows
    :return: SVG string for the figure
    """
    angle_rad = math.radians(angle)
    dx = arrow_length * math.cos(angle_rad)
    dy = arrow_length * math.sin(angle_rad)
    
    # Main line
    figure = f'<line x1="{x - line_length//2}" y1="{y}" ' \
             f'x2="{x + line_length//2}" y2="{y}" ' \
             f'stroke="black" stroke-width="{line_thickness}"/>'
    
    # Arrow lines
    if direction == 'out':
        figure += f'<line x1="{x - line_length//2}" y1="{y}" ' \
                  f'x2="{x - line_length//2 - dx}" y2="{y - dy}" ' \
                  f'stroke="black" stroke-width="{line_thickness}"/>'
        figure += f'<line x1="{x - line_length//2}" y1="{y}" ' \
                  f'x2="{x - line_length//2 - dx}" y2="{y + dy}" ' \
                  f'stroke="black" stroke-width="{line_thickness}"/>'
        figure += f'<line x1="{x + line_length//2}" y1="{y}" ' \
                  f'x2="{x + line_length//2 + dx}" y2="{y - dy}" ' \
                  f'stroke="black" stroke-width="{line_thickness}"/>'
        figure += f'<line x1="{x + line_length//2}" y1="{y}" ' \
                  f'x2="{x + line_length//2 + dx}" y2="{y + dy}" ' \
                  f'stroke="black" stroke-width="{line_thickness}"/>'
    else:  # 'in'
        figure += f'<line x1="{x - line_length//2}" y1="{y}" ' \
                  f'x2="{x - line_length//2 + dx}" y2="{y - dy}" ' \
                  f'stroke="black" stroke-width="{line_thickness}"/>'
        figure += f'<line x1="{x - line_length//2}" y1="{y}" ' \
                  f'x2="{x - line_length//2 + dx}" y2="{y + dy}" ' \
                  f'stroke="black" stroke-width="{line_thickness}"/>'
        figure += f'<line x1="{x + line_length//2}" y1="{y}" ' \
                  f'x2="{x + line_length//2 - dx}" y2="{y - dy}" ' \
                  f'stroke="black" stroke-width="{line_thickness}"/>'
        figure += f'<line x1="{x + line_length//2}" y1="{y}" ' \
                  f'x2="{x + line_length//2 - dx}" y2="{y + dy}" ' \
                  f'stroke="black" stroke-width="{line_thickness}"/>'
    
    return figure

def create_muller_lyer_comparison_svg(width, height, line_length1, line_length2, arrow_length, angle, line_thickness):
    """
    Generate an SVG with two Müller-Lyer figures in a staggered over-under arrangement.
    
    :param width: SVG width
    :param height: SVG height
    :param line_length1: Length of the first main line
    :param line_length2: Length of the second main line
    :param arrow_length: Length of the arrow lines
    :param angle: Angle of the arrow lines in degrees
    :param line_thickness: Thickness of the lines
    :return: SVG string
    """
    svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
    
    # First figure (arrows pointing outward) - top left
    svg += create_muller_lyer_figure(width // 3, height // 3, line_length1, arrow_length, angle, line_thickness, 'out')
    
    # Second figure (arrows pointing inward) - bottom right
    svg += create_muller_lyer_figure(2 * width // 3, 2 * height // 3, line_length2, arrow_length, angle, line_thickness, 'in')
    
    svg += '</svg>'
    return svg


def generate_illusions_for_day(day, num_illusions=10):
    """
    Generate a set of Müller-Lyer comparison illusions for a specific day.
    
    :param day: The day number of the experiment
    :param num_illusions: Number of illusions to generate
    :return: A list of dictionaries containing illusion data
    """
    illusions = []
    
    # Base parameters
    width = 600
    height = 400
    base_line_length = 200  # We'll keep this as is for screen display
    arrow_length = 20  # Adjusted to be proportional to the original 10mm
    angle = 36  # Angle from the original study
    line_thickness = 2
    
    # Generate illusions with the same length
    for i in range(num_illusions // 2):
        line_length = base_line_length + random.randint(-20, 20)
        
        svg = create_muller_lyer_comparison_svg(width, height, line_length, line_length, 
                                                arrow_length, angle, line_thickness)
        
        illusion_data = {
            "day": day,
            "illusion_number": i + 1,
            "svg_filename": f"muller_lyer_day{day}_illusion{i+1}.svg",
            "svg": svg,
            "line_length1": line_length,
            "line_length2": line_length,
            "actual_difference": 0,
            "arrow_length": arrow_length,
            "angle": angle,
            "line_thickness": line_thickness,
            "same_length": True
        }
        
        illusions.append(illusion_data)
    
    # Generate illusions with different lengths
    for i in range(num_illusions // 2, num_illusions):
        line_length1 = base_line_length + (random.randint(-4, 4) * 5)
        line_length2 = base_line_length + (random.randint(-4, 4) * 5)
        while line_length1 == line_length2:  # Ensure different lengths
            line_length2 = base_line_length + (random.randint(-4, 4) * 5)
        
        actual_difference = line_length1 - line_length2
        
        svg = create_muller_lyer_comparison_svg(width, height, line_length1, line_length2, 
                                                arrow_length, angle, line_thickness)
        
        illusion_data = {
            "day": day,
            "illusion_number": i + 1,
            "svg_filename": f"muller_lyer_day{day}_illusion{i+1}.svg",
            "svg": svg,
            "line_length1": line_length1,
            "line_length2": line_length2,
            "actual_difference": actual_difference,
            "arrow_length": arrow_length,
            "angle": angle,
            "line_thickness": line_thickness,
            "same_length": False
        }
        
        illusions.append(illusion_data)
    
    # Shuffle the illusions to randomize the order
    random.shuffle(illusions)
    
    # Update illusion numbers after shuffling
    for i, illusion in enumerate(illusions):
        illusion["illusion_number"] = i + 1
        illusion["svg_filename"] = f"muller_lyer_day{day}_illusion{i+1}.svg"
    
    return illusions

def save_illusions_and_metadata(illusions, day):
    """
    Save the generated SVGs and create a metadata file.
    
    :param illusions: List of illusion data dictionaries
    :param day: The day number of the experiment
    """
    for illusion in illusions:
        svg_filename = illusion["svg_filename"]
        with open(svg_filename, "w") as f:
            f.write(illusion["svg"])
    
    # Create a copy of illusions without the SVG string for the metadata file
    metadata = [{k: v for k, v in illusion.items() if k != 'svg'} for illusion in illusions]
    
    metadata_filename = f"muller_lyer_day{day}_metadata.json"
    with open(metadata_filename, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Generated {len(illusions)} illusions for day {day}")
    print(f"Metadata saved to {metadata_filename}")

# Example usage
if __name__ == "__main__":
    for day in range(1, 6):  # Generate illusions for 5 days
        illusions = generate_illusions_for_day(day)
        save_illusions_and_metadata(illusions, day)