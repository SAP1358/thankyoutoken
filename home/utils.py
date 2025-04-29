import openpyxl
from datetime import datetime
from ftplib import FTP, error_perm
from PIL import Image
from io import BytesIO
from myprofile.models import BefInsUcmsg


def process_excel_data(file):
    wb = openpyxl.load_workbook(file)
    ws = wb.active

    create_flag = False
    today = datetime.now().strftime('%Y-%m-%d')

    for row in ws.iter_rows(min_row=2, values_only=True):
        send_company, send_department, send_username, send_empname, \
        recv_company, recv_department, recv_username, recv_empname, \
        send_time, send_content, images_id,  *extra_columns = row
        
        if extra_columns:
            next_column_value = extra_columns[0]
            if next_column_value == 'R':
                # 처리할 내용 추가
                pass
            else:
                # 다른 처리 내용 추가
                pass
        else:

            # 데이터베이스에 중복되는지 확인
            if not BefInsUcmsg.objects.filter(
                send_company=send_company,
                send_department=send_department,
                send_username=send_username,
                send_empname=send_empname,
                recv_company=recv_company,
                recv_department=recv_department,
                recv_username=recv_username,
                recv_empname=recv_empname,
                send_time=send_time,
                send_content=send_content,
                images_id = images_id,
                reg_date__icontains=today
            ).exists():
                # 중복되는 데이터가 없으면 데이터베이스에 저장
                BefInsUcmsg.objects.create(
                    send_company=send_company,
                    send_department=send_department,
                    send_username=send_username,
                    send_empname=send_empname,
                    recv_company=recv_company,
                    recv_department=recv_department,
                    recv_username=recv_username,
                    recv_empname=recv_empname,
                    send_time=send_time,
                    send_content=send_content,
                    reg_date =datetime.now(),
                    images_id =images_id,
                    insert_yn = 'R'
                )
                
                create_flag = True

    return create_flag


def compress_image(file):
    img = Image.open(file)

    # Convert RGBA to RGB if needed
    img = img.convert("RGB")

    # Calculate dimensions to maintain aspect ratio
    max_width = 1280
    if img.width > max_width:
        ratio = max_width / img.width
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create a BytesIO object to store the compressed image
    img_io = BytesIO()

    # Set initial quality
    quality = 30
    max_size = 100 * 1024  # 100KB

    while quality > 5:
        img_io.seek(0)
        img_io.truncate(0)
        img.save(img_io, format="JPEG", quality=quality, optimize=True)

        # Check if size is less than max_size
        if img_io.tell() <= max_size:
            break

        # Reduce quality and try again
        quality -= 5

    img_io.seek(0)
    return img_io


def create_nested_dir(ftp, path):
    dirs = path.split("/")
    for i in range(1, len(dirs) + 1):
        current_path = "/".join(dirs[:i])
        try:
            ftp.mkd(current_path)
        except error_perm as e:
            if "550" in str(e):
                continue
            else:
                raise


def upload_to_cdn(file_obj, sub_path, file_name):
    try:
        # Connect to CDN server via FTP
        ftp = FTP()
        ftp.connect(host="upload.myskcdn.net", port=2200)
        ftp.login(user="woori", passwd="!@Wooribank09")

        # Create file path
        file_path = f"wooribank-test/thankyou/media/user/{sub_path}"
        print(file_path)

        try:
            # Change directory to file path
            ftp.cwd(file_path)
        except error_perm as e:
            # Make directory if not exist
            if "550" in str(e):
                create_nested_dir(ftp, file_path)
                ftp.cwd(file_path)
            else:
                raise

        # Upload image
        ftp.storbinary(f"STOR {file_name}", file_obj)

        # Disconnect FTP
        ftp.quit()

        return f"https://cdn.wooriwbn.com/{file_path}/{file_name}"
    except Exception as e:
        print(f"Failed to upload file: {e}")
