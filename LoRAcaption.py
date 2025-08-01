import glob
import os
from PIL import Image
from PIL import ImageOps
import numpy as np
import torch
import comfy

class LoRACaptionSave:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
				"namelist": ("STRING", {"forceInput": True}),
                "path": ("STRING", {"forceInput": True}),
                "text": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "prefix": ("STRING", {"default": " "}),
            }
        }

    OUTPUT_NODE = True
    RETURN_TYPES = ()
    FUNCTION = "save_text_file"
    CATEGORY = "LJRE/LORA"

    def save_text_file(self, text, path, namelist, prefix):

        if not os.path.exists(path):
            cstr(f"The path `{path}` doesn't exist! Creating it...").warning.print()
            try:
                os.makedirs(path, exist_ok=True)
            except OSError as e:
                cstr(f"The path `{path}` could not be created! Is there write access?\n{e}").error.print()

        if text.strip() == '':
            cstr(f"There is no text specified to save! Text is empty.").error.print()

        namelistsplit = namelist.splitlines()
        namelistsplit = [i[:-4] for i in namelistsplit]
        
        
        if prefix.endswith(","):
            prefix += " "
        elif not prefix.endswith(", "):
            prefix+= ", "
        
        file_extension = '.txt'
        filename = self.generate_filename(path, namelistsplit, file_extension)
        
        file_path = os.path.join(path, filename)
        self.writeTextFile(file_path, text, prefix)

        return (text, { "ui": { "string": text } } )
        
    def generate_filename(self, path, namelistsplit, extension):
        counter = 1
        filename = f"{namelistsplit[counter-1]}{extension}"
        while os.path.exists(os.path.join(path, filename)):
            counter += 1
            filename = f"{namelistsplit[counter-1]}{extension}"

        return filename

    def writeTextFile(self, file, content, prefix):
        try:
            with open(file, 'w', encoding='utf-8', newline='\n') as f:
                content= prefix + content
                f.write(content)
        except OSError:
            cstr(f"Unable to save file `{file}`").error.print()

def io_file_list(dir='',pattern='*.txt'):
    res=[]
    for filename in glob.glob(os.path.join(dir,pattern)):
        res.append(filename)
    return res

			
class LoRACaptionLoad:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
         return {
            "required": {
                "path": ("STRING", {"default":""}),			
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "IMAGE",)
    RETURN_NAMES = ("Name list", "path", "Image list",)

    FUNCTION = "captionload"

    #OUTPUT_NODE = False

    CATEGORY = "LJRE/LORA"

    def captionload(self, path):
        # Step 1: Bildnamen (namelist) erstellen
        valid_extensions = ['.png', '.jpg', '.jpeg', '.webp']
        dir_files = os.listdir(path)
        dir_files = [f for f in dir_files if any(f.lower().endswith(ext) for ext in valid_extensions)]
        namelist = '\n'.join(dir_files)

        # Step 2: Bilddaten laden
        image_paths = [os.path.join(path, x) for x in dir_files]

        if len(image_paths) == 0:
            raise FileNotFoundError("No valid image files found in the directory.")

        images = []
        for image_path in image_paths:
            if os.path.isdir(image_path):
                continue
            try:
                i = Image.open(image_path)
                i = ImageOps.exif_transpose(i)
                image = i.convert("RGB")
                image = np.array(image).astype(np.float32) / 255.0
                image = torch.from_numpy(image)[None,]
                images.append(image)
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")

        if len(images) == 0:
            raise FileNotFoundError("No valid images could be loaded.")

        # Wenn mehrere Bilder, bring sie auf gleiche Gr��e
        if len(images) == 1:
            image1 = images[0]
        else:
            image1 = images[0]
            for image2 in images[1:]:
                if image1.shape[1:] != image2.shape[1:]:
                    image2 = comfy.utils.common_upscale(
                        image2.movedim(-1, 1),
                        image1.shape[2],
                        image1.shape[1],
                        "bilinear",
                        "center"
                    ).movedim(1, -1)
                image1 = torch.cat((image1, image2), dim=0)

        return namelist, path, image1, len(images)
