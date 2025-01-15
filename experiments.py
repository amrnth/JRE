import cv2
import os 
import subprocess
from matplotlib import pyplot as plt
import os
import multiprocessing
import psutil
from PIL import Image, ImageFilter, ImageEnhance

def has_cuda_gpu():
   return cv2.cuda.getCudaEnabledDeviceCount()

# Function to extract frames from the video
def extract_frames(input_video, frame_dir):
    if not os.path.exists(frame_dir):
        os.makedirs(frame_dir)
    subprocess.call([
        'ffmpeg',
        '-i', input_video,
        '-vf', 'scale=-1:720',
        f'{frame_dir}/frame%04d.png'
    ])

def check_free_cores():
    
    total_cores = multiprocessing.cpu_count()
    cpu_usage = psutil.cpu_percent(percpu=True)
    free_cores = sum(1 for usage in cpu_usage if usage < 30)  # Consider core "free" if usage < 30%
    
    print({
        'total_cores': total_cores,
        'free_cores': free_cores,
        'cpu_usage': cpu_usage
    })

class FrameProcessor:
    def __init__(self, target_size=(1080, 1920), sample_frame="data_dump/frames/frame0808.png"):
        self.target_size = target_size
        self.enhancements = {
            'blur': ImageFilter.GaussianBlur,
            'brightness': ImageEnhance.Brightness,
            'contrast': ImageEnhance.Contrast,
            'color': ImageEnhance.Color,
            'sharpness': ImageEnhance.Sharpness
        }
        self.sample_frame =sample_frame

    def apply_blur(self, img, radius=10):
        return img.filter(self.enhancements['blur'](radius=radius))

    def apply_brightness(self, img, factor=1.2):
        enhancer = self.enhancements['brightness'](img)
        return enhancer.enhance(factor)

    def apply_contrast(self, img, factor=1.2):
        enhancer = self.enhancements['contrast'](img)
        return enhancer.enhance(factor)

    def apply_color(self, img, factor=1.2):
        enhancer = self.enhancements['color'](img)
        return enhancer.enhance(factor)

    def apply_sharpness(self, img, factor=1.2):
        enhancer = self.enhancements['sharpness'](img)
        return enhancer.enhance(factor)

    def create_enhanced_background(self, img: Image.Image, enhancements=None) -> Image.Image:
        if enhancements is None:
            enhancements = {'blur': 10}  # default enhancement

        enhanced_img = img.copy()
        for enhancement in enhancements:
            if enhancement["type"] == 'blur':
                enhanced_img = self.apply_blur(enhanced_img, enhancement["factor"])
            elif enhancement["type"] == 'brightness':
                enhanced_img = self.apply_brightness(enhanced_img, enhancement["factor"])
            elif enhancement["type"] == 'contrast':
                enhanced_img = self.apply_contrast(enhanced_img, enhancement["factor"])
            elif enhancement["type"] == 'color':
                enhanced_img = self.apply_color(enhanced_img, enhancement["factor"])
            elif enhancement["type"] == 'sharpness':
                enhanced_img = self.apply_sharpness(enhanced_img, enhancement["factor"])

        new_width_exploded = int(self.target_size[1]*self.target_size[1]/self.target_size[0])
        new_height_exploded = self.target_size[1]
        enhanced_img = enhanced_img.resize((new_width_exploded, new_height_exploded))
        enhanced_img = enhanced_img.crop((
            new_width_exploded//2 - self.target_size[0]//2, 
            0, 
            new_width_exploded//2 + self.target_size[0]//2, 
            self.target_size[1]
        ))
        return enhanced_img

    

    def process_frame(self, img: Image.Image, enhancements=None) -> Image.Image:
        original_width, original_height = img.size
        img = img.convert('RGB')

        # Create enhanced background
        enhanced_bg = self.create_enhanced_background(img, enhancements)

        # Resize original frame
        scale_factor = self.target_size[0] / original_width
        new_width = self.target_size[0]
        new_height = int(original_height * scale_factor)
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        # Paste resized image onto enhanced background
        paste_y = (self.target_size[1] - new_height) // 2
        enhanced_bg.paste(resized_img, (0, paste_y))

        # Add green border
        # draw = ImageDraw.Draw(enhanced_bg)
        # draw.rectangle([0, 0, self.target_size[0]-1, self.target_size[1]-1], outline='green', width=50)

        return enhanced_bg
    
    def create_enhancement_experiments(self):
        if not os.path.exists('enhancement_experiments'):
            os.makedirs('enhancement_experiments')

        img = Image.open(self.sample_frame)
        
        # Define enhancement types and their ranges
        enhancements = {
            'blur': [10, 20, 30, 40, 50, 60],
            'brightness': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'contrast': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'color': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'sharpness': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        }

        for enhance_type, factors in enhancements.items():
            # Calculate figure size to maintain 1080x1920 aspect ratio for each subplot
            subplot_width = 1080/100  # Convert pixels to inches assuming 100 DPI
            subplot_height = 2* 1920/100
            fig_width = subplot_width * 3  # 6 subplots
            
            fig = plt.figure(figsize=(fig_width, subplot_height))
            for idx, factor in enumerate(factors, 1):
                ax = plt.subplot(2, 3, idx)
                temp = img.copy()
                enhancement = {'type': enhance_type, 'factor': factor}
                processed = self.process_frame(temp, [enhancement])
                plt.imshow(processed)
                plt.title(f'Factor: {factor}', fontdict={
                    "fontsize": 40
                })
                plt.axis('off')
                
                # Set aspect ratio to be exact
                ax.set_aspect('equal')
            
            plt.subplots_adjust(wspace=0.05)
            plt.suptitle(enhance_type.capitalize(), fontsize=60, y=0.98)
            plt.savefig(f'enhancement_experiments/{enhance_type}_comparison.png', 
                   bbox_inches='tight', pad_inches=0.3, dpi=100)
            plt.close()

    def create_blur_brightness_grid(self):
        if not os.path.exists('enhancement_experiments'):
            os.makedirs('enhancement_experiments')

        img = Image.open(self.sample_frame)
        blur_values = [30, 40, 50]
        brightness_values = [0.3, 0.4, 0.5, 0.6]

        rows = len(blur_values)
        cols = len(brightness_values)
        
        subplot_height = 1920/100
        subplot_width = 1080/100
        fig_height =  rows * 1920/100
        fig_width = subplot_width * 3
        
        fig = plt.figure(figsize=(fig_width, subplot_height))
        
        for idx, (blur, brightness) in enumerate([(b, br) for b in blur_values for br in brightness_values], 1):
            ax = plt.subplot(rows, cols, idx)
            temp = img.copy()
            enhancements = [
                {'type': 'blur', 'factor': blur},
                {'type': 'brightness', 'factor': brightness}
            ]
            processed = self.process_frame(temp, enhancements)
            plt.imshow(processed)
            plt.title(f'Blur: {blur}, Brightness: {brightness}', fontdict={"fontsize": 40})
            plt.axis('off')
            ax.set_aspect('equal')
        
        plt.subplots_adjust(wspace=0.05)
        plt.suptitle('Blur + Brightness Combinations', fontsize=60, y=0.98)
        plt.savefig('enhancement_experiments/blur_brightness_grid.png',
                    bbox_inches='tight', pad_inches=0.3, dpi=100)
        plt.close()

    def create_zoom_grid(self):
        w_bg, h_bg = self.target_size
        bg = Image.new("RGB", (w_bg, h_bg), color = "red")

        img = Image.open(self.sample_frame)
        
        fig_height = 2*1920/100
        fig_width = 3*1080/100
        fig = plt.figure(figsize=(fig_width, fig_height))

        for i in range(6):
            img_copy = img.copy()
            w, h = img_copy.size
            zoom_factor = 1 + i*0.2
            w1, h1 = int(zoom_factor * w), int(zoom_factor * h)
            img_copy = img_copy.resize((w1, h1), Image.LANCZOS)

            img_copy = img_copy.crop(((w1-w_bg)//2, 0, (w1+w_bg)//2, h1))

            bg.paste(img_copy, (0, (h_bg - h1)//2))

            ax = plt.subplot(2, 3, i+1)
            plt.imshow(bg)
            plt.axis("off")
            plt.title(f"factor: {zoom_factor}", fontdict={
                "fontsize": 40
            })

            ax.set_aspect("equal")
        
        plt.subplots_adjust(wspace=0.05)
        plt.suptitle("Zoom test")
        plt.savefig("enhancement_experiments/zoom.png", bbox_inches='tight', pad_inches=0.3, dpi=100)


from PIL import Image, ImageDraw, ImageFont
import os

class ResolutionImageProcessor:
    def __init__(self, font_path="arial.ttf", font_size=40, output_dir="output_images", background_size=(1080, 1920)):
        # List of major video resolutions
        self.resolutions = [
            (320, 240),   # QVGA
            (640, 480),   # VGA
            (800, 600),   # SVGA
            (1024, 768),  # XGA
            (1280, 720),  # 720p HD
            (1920, 1080), # 1080p Full HD
            (2560, 1440), # 1440p QHD
            (3840, 2160), # 4K UHD
            (7680, 4320), # 8K UHD
        ]
        
        # Font settings for the resolution text
        self.font_size = font_size
        # Load the font
        self.font = ImageFont.truetype(font_path, self.font_size)
        
        # Output directory for the final images
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # White background image size
        self.background_width, self.background_height = background_size

    def process_resolution(self, width, height):
        # Step 1: Create a red image with the given resolution
        red_image = Image.new('RGB', (width, height), color='red')
        
        # Step 2: Draw the resolution text in white at the center
        draw = ImageDraw.Draw(red_image)
        text = f"{width}x{height}"
        bbox = draw.textbbox((0,0), text, font=self.font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        text_x = (width - text_width) / 2
        text_y = (height - text_height) / 2
        draw.text((text_x, text_y), text, font=self.font, fill='white')
        
        # Step 3: Create a white background image of 1080x1920
        background = Image.new('RGB', (self.background_width, self.background_height), color='white')
        
        # Step 4: Resize the red image so its width is 1080, maintaining aspect ratio
        new_red_width = self.background_width
        aspect_ratio = height / width
        new_red_height = int(new_red_width * aspect_ratio)
        resized_red_image = red_image.resize((new_red_width, new_red_height))
        
        # Step 5: Calculate the position to center the resized red image on the background
        paste_x = 0  # Since width is set to 1080
        paste_y = (self.background_height - new_red_height) // 2
        
        # Step 6: Paste the resized red image onto the background
        background.paste(resized_red_image, (paste_x, paste_y))
        
        # Step 7: Save the final image with a filename indicating the original resolution
        filename = f"{width}x{height}.png"
        output_path = os.path.join(self.output_dir, filename)
        background.save(output_path)
        print(f"Saved {output_path}")

    def process_all_resolutions(self):
        for width, height in self.resolutions:
            self.process_resolution(width, height)
            self.process_resolution(height, width)
        print("All images have been processed and saved.")


def rename_files_sequentially(output_dir):
    # Get all .png files in the directory
    files = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
    
    # Rename files to follow the pattern frame0001.png, frame0002.png, etc.
    for idx, filename in enumerate(files, start=1):
        new_name = f"frame{idx:04d}.png"
        os.rename(os.path.join(output_dir, filename), os.path.join(output_dir, new_name))
        print(f"Renamed {filename} to {new_name}")


class FontExperimentation:
    def __init__(self, output_dir="data_dump/output_font_images", image_size=(1080, 1920), text="Sample Text", font_size=100, text_color="black", background_color="white"):
        self.output_dir = output_dir
        self.image_size = image_size
        self.text = text
        self.font_size = font_size
        self.text_color = text_color
        self.background_color = background_color
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def add_text_to_image(self, image, font_path):
        try:
            font = ImageFont.truetype(font_path, self.font_size)
        except IOError:
            print(f"Font file not found or invalid: {font_path}")
            return None

        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), self.text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = (
            (self.image_size[0] - text_width) / 2,
            (self.image_size[1] - text_height) / 2
        )
        draw.text(position, self.text, font=font, fill=self.text_color)
        return image

    def generate_images_for_fonts(self, font_paths):
        for font_path in font_paths:
            font_name = os.path.basename(font_path).split('.')[0]
            img = Image.new('RGB', self.image_size, color=self.background_color)
            img_with_text = self.add_text_to_image(img, font_path)
            if img_with_text:
                output_path = os.path.join(self.output_dir, f"{font_name}.png")
                img_with_text.save(output_path)
                print(f"Saved image with font: {font_name}")
            else:
                print(f"Skipped font: {font_name}")

    def run_expt():
        fonts = os.listdir("data_dump/fonts")
        fonts_path = []
        for font in fonts:
            for f in os.listdir("data_dump/fonts/"+font):
                if(f.endswith(".ttf") or f.endswith(".otf")):
                    fonts_path.append("data_dump/fonts/"+font+"/"+f)
                    # break
        print(fonts_path)
        processor = FontExperimentation()
        processor.generate_images_for_fonts(fonts_path)

class ImageFilterExperimentation:
    def __init__(self, image_path="data_dump/frames/frame0808.png"):
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.filters = [
            ImageFilter.BoxBlur(radius=20),
            ImageFilter.BoxBlur(radius=35),
            ImageFilter.BoxBlur(radius=50),
            ImageFilter.GaussianBlur(radius=20),
            ImageFilter.GaussianBlur(radius=35),
            ImageFilter.GaussianBlur(radius=50),
        ]

    def apply_filters(self):
        filtered_images = []
        filter_names = []
        
        for filter_type in self.filters:
            filtered = self.image.copy()
            filtered = filtered.filter(filter_type)
            filtered_images.append(filtered)
            filter_names.append(str(filter_type).split('.')[-1])
        
        return filtered_images, filter_names

    def create_grid(self):
        filtered_images, filter_names = self.apply_filters()
        rows = (len(filtered_images) + 2) // 3  # Calculate rows needed for grid
        cols = min(3, len(filtered_images))
        
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(rows, cols, figsize=(15, 5*rows))
        axes = axes.flatten() if rows > 1 else [axes] if cols == 1 else axes
        
        for idx, (img, name) in enumerate(zip(filtered_images, filter_names)):
            axes[idx].imshow(img)
            axes[idx].set_title(name+"- R"+str(20+15*(idx%3)))
            axes[idx].axis('off')
        
        # Hide any empty subplots
        for idx in range(len(filtered_images), len(axes)):
            axes[idx].axis('off')
        
        plt.tight_layout()
        plt.savefig('filter_comparison.png')
        plt.close()
    
    def run_expt():
        processor = ImageFilterExperimentation()
        processor.create_grid()

def temp():
    for dir in os.listdir("processed_data"):
        print("\"https://youtube.com/watch?v=", dir, "\",", sep="")
        # for file in os.listdir("processed_data/"+dir):
        #     if(file=="final_video_subbed.mp4"):
        #         path = os.path.join("processed_data", dir, "final_video_subbed.mp4")

        #         new_path = os.path.join("processed_data", dir, "final_video_subbed_1.mp4")
        #         os.rename(path, new_path)


# Example usage:
if __name__ == "__main__":
    # processor = ResolutionImageProcessor()
    # processor.process_all_resolutions()
    # output_dir = "output_images"
    # rename_files_sequentially(output_dir)
    # img = Image.open("data_dump/frames/frame0808.png")
    # new_img = process_frame(img)
    # new_img.save("frame_processing_test.png")
    # ImageFilterExperimentation.run_expt()
    # fp = FrameProcessor()
    # fp.create_zoom_grid()
    # fp.create_enhancement_experiments()
    # fp.create_blur_brightness_grid()
    # print(check_free_cores())
    temp()
