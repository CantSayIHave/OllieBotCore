import asyncio
from PIL import Image, ImageDraw, ImageOps
import cv2
import os


class FoundFace:
    def __init__(self, rect):
        self.x_pos = rect[0]
        self.y_pos = rect[1]
        self.width = rect[2]
        self.height = rect[3]

    def __str__(self):
        return 'FoundFace:[x={},y={},w={},h={}]'.format(self.x_pos,
                                                        self.y_pos,
                                                        self.width,
                                                        self.height)

    def __repr__(self):
        return self.__str__()


class StickerProfile:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'sticker')  # used for file name, info
        self.data_type = kwargs.get('data_type', 'human')  # purely profile info
        self.fp = kwargs.get('fp', '')
        self.scale = kwargs.get('scale', 0.6)
        self.sticker_x = kwargs.get('sticker_x', None)
        self.sticker_y = kwargs.get('sticker_y', None)

    def __str__(self):
        return 'StickerProfile:[n={},d={},s={},im={}]'.format(self.name,
                                                              self.data_type,
                                                              self.scale,
                                                              self.fp)

    def __repr__(self):
        return self.__str__()


async def apply_sticker(base_image: Image,
                        human_profile: StickerProfile,
                        anime_profile: StickerProfile,
                        default_profile: StickerProfile,
                        loop,
                        executor):

    def find_faces():
        faceCascade = cv2.CascadeClassifier('resources/haarcascade_frontalface_default.xml')
        cv_image = cv2.imread('base_image.png')
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=1,
            minSize=(100, 100),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) > 0:
            return [FoundFace(x) for x in faces]
        else:
            return []

    def find_anime_faces():
        faceCascade = cv2.CascadeClassifier('resources/lbpcascade_animeface.xml')
        cv_image = cv2.imread('base_image.png')
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=1,
            minSize=(100, 100)
            # flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) > 0:
            return [FoundFace(x) for x in faces]
        else:
            return []

    found_human_faces = None
    found_anime_faces = None
    found_faces = None

    # attempt to prevent multiple threads overwriting base image
    # requires immediate removal of base image after testing
    while os.path.isfile('base_image.png'):
        await asyncio.sleep(0.1)

    base_image.save('base_image.png')

    try:
        found_human_faces = await loop.run_in_executor(executor, find_faces)
        found_anime_faces = await loop.run_in_executor(executor, find_anime_faces)
        try:
            os.remove('base_image.png')
        except:
            pass
    except Exception as e:
        print('Face detection failed at: ' + str(e))
        try:
            os.remove('base_image.png')
        except:
            pass

    # select better dataset
    # for now, "better" is more face matches, defaults to anime because internet
    if len(found_human_faces) > len(found_anime_faces):
        found_faces = found_human_faces
        correct_profile = human_profile
    else:
        found_faces = found_anime_faces
        correct_profile = anime_profile

    if found_faces:
        for face in found_faces:  # type:FoundFace
            overlay = Image.open(correct_profile.fp)

            # scale overlay to face, proportionally
            overlay = resize_overlay(overlay, face=face)

            # scale overlay by profile scale constant
            overlay = overlay.resize((int(overlay.size[0] * correct_profile.scale),
                                      int(overlay.size[1] * correct_profile.scale)),
                                     Image.ANTIALIAS)

            paste_x = face.x_pos
            paste_y = face.y_pos

            if correct_profile.sticker_x:
                paste_x = int(correct_profile.sticker_x(overlay, face))

            if correct_profile.sticker_y:
                paste_y = int(correct_profile.sticker_y(overlay, face))

            base_image = base_image.convert("RGBA")
            overlay = overlay.convert("RGBA")

            base_image.paste(overlay, (paste_x, paste_y), overlay)
    else:
        overlay = Image.open(correct_profile.fp)

        # scale overlay to base image, proportionally
        overlay = resize_overlay(overlay, to_image=base_image)

        # scale overlay by profile scale constant
        overlay = overlay.resize((int(overlay.size[0] * default_profile.scale),
                                  int(overlay.size[1] * default_profile.scale)),
                                 Image.ANTIALIAS)

        paste_x = 0
        paste_y = 0

        # only 'face' is whole base image
        dummy_face = FoundFace((0, 0, base_image.size[0], base_image.size[1]))

        if default_profile.sticker_x:
            paste_x = int(default_profile.sticker_x(overlay, dummy_face))

        if default_profile.sticker_y:
            paste_y = int(default_profile.sticker_y(overlay, dummy_face))

        base_image = base_image.convert("RGBA")
        overlay = overlay.convert("RGBA")

        base_image.paste(overlay, (paste_x, paste_y), overlay)

    result_name = '{}.png'.format(correct_profile.name)

    base_image.save(result_name, format='PNG')
    return result_name


def resize_overlay(overlay: Image, face: FoundFace = None, to_image: Image = None) -> Image:
    if to_image:
        to_width, to_height = to_image.size
    else:
        to_width, to_height = face.width, face.height

    # scale overlay to face rectangle by face width
    if overlay.size[0] > to_width:
        new_width = to_width
        new_height = new_width * (overlay.size[1] / overlay.size[0])
        overlay = overlay.resize((int(new_width), int(new_height)),
                                 Image.ANTIALIAS)

    # scale overlay to face rectangle by face height
    if overlay.size[1] > to_height:
        new_height = to_height
        new_width = new_height * (overlay.size[0] / overlay.size[1])
        overlay = overlay.resize((int(new_width), int(new_height)),
                                 Image.ANTIALIAS)

    return overlay
