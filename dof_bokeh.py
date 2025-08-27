import argparse
import cv2
import numpy as np
import torch
import argparse
import cv2
import numpy as np
import torch
import os
from PIL import Image

# Zer0-Day Bokeh: Cybernetic Depth Field Adjuster
#
# Your vision, sharpened.

def load_depth_model(device):
    """
    Loads the MiDaS depth estimation model and its transforms.
    Returns a tuple (model, transform).
    """
    print("Loading MiDaS model...")
    try:
        model_type = "MiDaS_small"
        model = torch.hub.load("intel-isl/MiDaS", model_type, pretrained=True)
        model.to(device)
        model.eval()

        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
        transform = midas_transforms.small_transform if model_type == "MiDaS_small" else midas_transforms.dpt_transform

        return model, transform
    except Exception as e:
        print(f"Error loading MiDaS model: {e}")
        return None, None

def generate_depth_map(model, transform, image, device):
    """
    Generates a depth map from the input image using the MiDaS model.
    """
    # MiDaS requires specific preprocessing
    transform_input = transform(image).to(device)
    with torch.no_grad():
        prediction = model(transform_input)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=image.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()
    depth_map = prediction.cpu().numpy()

    # Normalize depth map to 0-1 range for consistency
    depth_map_normalized = (depth_map - np.min(depth_map)) / (np.max(depth_map) - np.min(depth_map))
    return depth_map_normalized


# Global variable to store click data for the preview window
click_data = {'x': -1, 'y': -1}

def mouse_callback(event, x, y, flags, param):
    """CV2 mouse callback function to capture click coordinates."""
    if event == cv2.EVENT_LBUTTONDOWN:
        click_data['x'] = x
        click_data['y'] = y
        print(f"Focus point selected at (x={x}, y={y})")

def get_focal_depth(args, depth_map):
    """
    Determines the focal depth based on user arguments.
    """
    if args.preview:
        print("Interactive preview enabled. Click on the image to set focus. Press any key to continue.")
        preview_window_name = "Zer0-Day Bokeh: Click to Focus"

        # Create a copy of the depth map for display, as a colorized version
        depth_display = (depth_map * 255).astype(np.uint8)
        depth_display_color = cv2.applyColorMap(depth_display, cv2.COLORMAP_MAGMA)

        cv2.namedWindow(preview_window_name)
        cv2.setMouseCallback(preview_window_name, mouse_callback)

        while True:
            cv2.imshow(preview_window_name, depth_display_color)
            key = cv2.waitKey(1) & 0xFF
            # Exit on any key press, after a click has been registered
            if key != 255 and click_data['x'] != -1:
                break

        cv2.destroyWindow(preview_window_name)

        # Use the clicked point to set the focal depth
        return depth_map[click_data['y'], click_data['x']]

    elif args.focus_percentile is not None:
        # Auto-focus at a certain percentile of the depth map
        focal_depth = np.percentile(depth_map, args.focus_percentile * 100)
        return focal_depth

    elif args.focus is not None:
        # Use a direct, normalized value
        return args.focus

    else:
        # Default to the center of the image if no focus method is specified
        h, w = depth_map.shape
        return depth_map[h // 2, w // 2]


def generate_bokeh_kernel(radius, blades, angle_rad):
    """Generates a bokeh kernel, circular or polygonal."""
    kernel = np.zeros((radius * 2 + 1, radius * 2 + 1))
    center = radius

    if blades == 0:  # Circular bokeh
        cv2.circle(kernel, (center, center), radius, (1, 1, 1), -1)
    else:  # Polygonal bokeh
        points = []
        for i in range(blades):
            theta = (2 * np.pi * i / blades) + angle_rad
            x = int(center + radius * np.cos(theta))
            y = int(center + radius * np.sin(theta))
            points.append((x, y))
        points = np.array(points, dtype=np.int32)
        cv2.fillConvexPoly(kernel, points, (1, 1, 1))

    # Normalize the kernel
    kernel /= np.sum(kernel)
    return kernel

def apply_bokeh_effect(image, depth_map, focal_depth, args):
    """
    Applies the bokeh effect to the image using the depth map.
    """
    # --- 1. Calculate Circle of Confusion (CoC) ---
    # `coc` is a map of blur amounts. 0 means in-focus, 1 means max blur.
    coc = np.abs(depth_map - focal_depth)
    coc = np.power(coc, 1.0 / (args.sharpness / 10.0)) # Apply sharpness

    # --- 2. Iterative Blurring ---
    # We blur the image iteratively with different kernel sizes.
    # This creates a more realistic and smoother DoF effect.

    # Convert image to float for processing
    img_float = image.astype(np.float32) / 255.0
    blurred_img = img_float.copy()

    # Number of blur levels to iterate through
    blur_levels = 10

    for i in range(blur_levels, 0, -1):
        # The radius for this level of blur
        radius = int(1 + (args.max_radius - 1) * (i / blur_levels))
        if radius % 2 == 0: radius += 1 # Kernel size must be odd

        # Create a mask for pixels that should get *at least* this much blur
        # The threshold is the CoC value corresponding to this blur radius
        coc_threshold = i / blur_levels
        mask = (coc >= coc_threshold).astype(np.uint8)

        # Generate the bokeh kernel for this radius
        kernel = generate_bokeh_kernel(radius, args.blades, np.deg2rad(args.angle))

        # Apply the blur
        blurred_level = cv2.filter2D(img_float, -1, kernel)

        # Blend this blur level into the result using the mask
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        blurred_img = np.where(mask_3ch == 1, blurred_level, blurred_img)

    # --- 3. Convert back to 8-bit image ---
    final_image = (blurred_img * 255).astype(np.uint8)

    return final_image


def main(args):
    """
    Main function to orchestrate the depth-of-field effect.
    """
    print("Initializing Zer0-Day Bokeh...")
    print(f"Input image: {args.input}")
    print("Backend: MiDaS")

    # --- 1. Load Image ---
    if not os.path.exists(args.input):
        print(f"Error: Input file not found at {args.input}")
        return

    image = cv2.imread(args.input)
    if image is None:
        print(f"Error: Could not read image from {args.input}")
        return

    print(f"Image loaded successfully. Shape: {image.shape}")

    # --- 2. Load Depth Model ---
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {DEVICE}")

    depth_model, transform = load_depth_model(DEVICE)
    if depth_model is None:
        return

    # --- 3. Get Depth Map ---
    depth_map = generate_depth_map(depth_model, transform, image, DEVICE)
    if depth_map is None:
        print("Error: Could not generate depth map.")
        return

    print(f"Depth map generated. Shape: {depth_map.shape}, Min: {depth_map.min()}, Max: {depth_map.max()}")

    # --- 4. Handle Focus ---
    focal_depth = get_focal_depth(args, depth_map)
    print(f"Focal depth set to: {focal_depth:.4f}")

    # --- 5. Apply Bokeh Effect ---
    output_image = apply_bokeh_effect(image, depth_map, focal_depth, args)
    print("Bokeh effect applied.")

    # --- 6. Save Output ---
    basename = os.path.splitext(os.path.basename(args.input))[0]
    output_filename = f"{basename}_bokeh.jpg"
    output_path = os.path.join(args.outdir, output_filename)

    cv2.imwrite(output_path, output_image)
    print(f"Output image saved to: {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Cyberpunk Image Depth of Field Adjuster")

    parser.add_argument('--input', type=str, required=True, help='Path to the input image.')
    parser.add_argument('--outdir', type=str, default='output', help='Directory to save the output image.')
    # Bokeh settings
    parser.add_argument('--blades', type=int, default=8, help='Number of aperture blades for bokeh shape (0 for circular). 8 is octagonal.')
    parser.add_argument('--angle', type=int, default=0, help='Rotation angle for polygonal bokeh.')
    parser.add_argument('--max_radius', type=int, default=28, help='Maximum blur radius.')
    parser.add_argument('--sharpness', type=int, default=12, help='Sharpness of the focus transition.')

    # Focus settings
    parser.add_argument('--preview', action='store_true', help='Enable interactive click-to-focus preview.')
    parser.add_argument('--focus_percentile', type=float, help='Set focus automatically at a depth percentile.')
    parser.add_argument('--focus', type=float, help='Set focus explicitly at a normalized depth value (0.0-1.0).')

    # Model-specific settings (like --bins for Depth Anything)
    parser.add_argument('--bins', type=int, default=10, help='Number of bins for some depth models.')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    main(args)
