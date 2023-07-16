from PIL import Image, ImageDraw, ImageFont
import exifread
import os

#为模仿风格，使用了小米字体
FONT = "./font/MiSans-Normal.ttf"
INPUT_DIR = "./input/"
OUTPUT_DIR = "./output/"
LOGO_DIR = "./logos/"


def get_exif(fname: str) -> dict:
    """
    获取图片的EXIF信息并返回一个包含关键信息的字典。

    参数：
    - fname：图片文件的路径

    返回值：
    包含以下关键信息的字典：
    {
        'CameraMaker': 相机制造商
        'Camera': 相机型号
        'DateTime': 拍摄时间
        'ExposureTime': 曝光时间
        'FNumber': 光圈值
        'ISOSpeedRatings': ISO感光度
        'FocalLength': 焦距
        '35mmFilm': 35mm等效焦距
        'ImageWidth': 图片宽度
        'ImageLength': 图片高度
        'Artist': 图片作者
    }
    如果某个字段无法获取，则对应的值为'UNKNOWN'或者空字符串。

    """
    exifInfo = {}

    with open(fname, "rb") as f:
        tags = exifread.process_file(f)

    exifInfo["CameraMaker"] = str(tags.get("Image Make", "UNKNOWN"))

    camera_model = str(tags.get("Image Model", "UNKNOWN"))
    if exifInfo["CameraMaker"] in camera_model:
        exifInfo["Camera"] = camera_model
    else:
        exifInfo["Camera"] = f"{exifInfo['CameraMaker']} {camera_model}"

    exifInfo["DateTime"] = str(tags.get("EXIF DateTimeOriginal", "UNKNOWN_TIME"))

    exposure_time = str(tags.get("EXIF ExposureTime", ""))
    exifInfo["ExposureTime"] = f"{exposure_time} " if exposure_time else ""

    fnumber = str(tags.get("EXIF FNumber", ""))
    exifInfo["FNumber"] = f"f/{fnumber}" if fnumber else "f/?"

    iso = str(tags.get("EXIF ISOSpeedRatings", ""))
    exifInfo["ISOSpeedRatings"] = f"ISO{iso}" if iso else "ISO???"

    focal_length = str(tags.get("EXIF FocalLength", ""))
    exifInfo["FocalLength"] = f"{focal_length}mm" if focal_length else "??mm"

    film_equivalent = str(tags.get("EXIF FocalLengthIn35mmFilm", ""))
    exifInfo["35mmFilm"] = f"({film_equivalent}mm)" if film_equivalent else ""

    exifInfo["ImageWidth"] = int(str(tags.get("EXIF ExifImageWidth", "0")))
    exifInfo["ImageLength"] = int(str(tags.get("EXIF ExifImageLength", "0")))

    exifInfo["Artist"] = "PHOTO BY " + str(tags.get("Image Artist", "SOMEBODY"))

    return exifInfo


def find_jpg_files(directory) -> list:
    """
    在给定的目录及其子目录中查找所有的 JPG 文件，并返回文件路径列表。

    参数：
    - directory：要搜索的目录的路径

    返回：
    - jpg_files：包含所有 JPG 文件路径的列表
    """

    jpg_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".jpg"):
                jpg_files.append(os.path.join(root, file))

    return jpg_files


def process_image(image_path, output_dir):
    """
    处理图像文件，添加文本和标志，并将修改后的图像保存到输出目录。

    参数：
    - image_path: 输入图像文件的路径
    - output_dir: 输出目录的路径

    返回：
    保存增加水印后的照片到指定的输出目录

    """
    print("正在处理：" + os.path.basename(image_path))

    # 获取图片的EXIF信息
    exif_info = get_exif(image_path)

    # 载入图片
    image = Image.open(image_path)

    # 读取照片长宽
    image_length = exif_info["ImageLength"]
    image_width = exif_info["ImageWidth"]

    # 创建底图
    if image_length < image_width:
        extra_height = int(image_length / 8)
    else:
        extra_height = int(image_width / 8)

    background_height = extra_height + image_length
    background_color = "white"
    background_image = Image.new("RGB", (image_width, background_height), background_color)

    # 设定水印信息
    lens_info_text = str(
        exif_info["FocalLength"]
        + exif_info["35mmFilm"]
        + " "
        + exif_info["FNumber"]
        + " "
        + exif_info["ExposureTime"]
        + " "
        + exif_info["ISOSpeedRatings"]
    )

    watermark_list = [
        {
            "text": exif_info["Camera"],
            "left": int(image_width / 40),
            "text_size": int(extra_height / 5),
            "top": int(image_length + (extra_height / 4)),
            "text_color": "black",
        },
        {
            "text": exif_info["DateTime"],
            "left": int(image_width / 40),
            "text_size": int(extra_height / 10),
            "top": int(image_length + (extra_height / 4) + int((extra_height / 5) * 1.5)),
            "text_color": "gray",
        },
        {
            "text": lens_info_text,
            "left": int(
                image_width
                - (
                    int(image_width / 40) * 2
                    + int(len(lens_info_text) * int(extra_height / 5) / 2)
                )
            ),
            "text_size": int(extra_height / 5),
            "top": int(image_length + (extra_height / 4)),
            "text_color": "black",
        },
        {
            "text": exif_info["Artist"],
            "left": int(
                image_width
                - (
                    int(image_width / 40) * 2
                    + int(len(lens_info_text) * int(extra_height / 5) / 2)
                )
            ),
            "text_size": int(extra_height / 10),
            "top": int(image_length + (extra_height / 4) + int(extra_height / 5) * 1.5),
            "text_color": "gray",
        },
    ]

    # 创建分割线
    guideline_length = (
        int((extra_height / 5) * 1.5) + int(extra_height / 10) + int(extra_height / 5)
    )
    guideline = Image.new("RGB", (5, guideline_length), "gray")
    guideline_top = int(image_length + (extra_height / 4) - int(extra_height / 5 / 2))
    guideline_left = int(
        image_width
        - (int(image_width / 40) * 2 + int(len(lens_info_text) * int(extra_height / 5) / 2))
        - int(extra_height / 5 / 2)
    )

    # 确认LOGO
    logo_path = os.path.join(LOGO_DIR, "%s.png" % str(exif_info["CameraMaker"]))

    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
    else:
        logo = Image.open(os.path.join(LOGO_DIR, "UNKNOW.png"))

    logo = logo.resize((guideline_length, guideline_length), 1)
    logo_top = guideline_top
    logo_left = guideline_left - int(extra_height / 5 / 2) - guideline_length

    # 合并底图
    background_image.paste(image, (0, 0))
    background_image.paste(guideline, (guideline_left, guideline_top))
    background_image.paste(logo, (logo_left, logo_top))

    # 开始绘制水印
    draw = ImageDraw.Draw(background_image)

    for i in range(len(watermark_list)):
        draw.text(
            (watermark_list[i]["left"], watermark_list[i]["top"]),
            watermark_list[i]["text"],
            watermark_list[i]["text_color"],
            font=ImageFont.truetype(FONT, watermark_list[i]["text_size"], encoding="utf-8"),
        )

    # 构造输出路径
    output_path = os.path.join(output_dir, os.path.basename(image_path))

    # 保存修改后的图片
    background_image.save(output_path, dpi=(300.0, 300.0), quality=100)


if __name__ == "__main__":
    # 创建输入目录（如果不存在）
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print("请先在input文件夹中放置照片，再重新运行本程序。")

    else:
        # 查找照片文件
        jpg_files = find_jpg_files(INPUT_DIR)
        
        if not jpg_files:
            print("在目录中没有找到照片文件。")
        else:
            # 打印发现的照片文件
            print("发现照片文件:")
            for jpg_file in jpg_files:
                print(os.path.basename(jpg_file))

            # 创建输出目录（如果不存在）
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            # 处理照片文件
            for jpg_file in jpg_files:
                process_image(jpg_file, OUTPUT_DIR)

            print("全部完成!")
