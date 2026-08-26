"""
modified from detect.py by K.Mimura

image folder should be as follows
- {base directory} <-- fixed path
    - {Yi}_{Xi}.jpg
    - {Yi}_{Xi}.jpg
    ...
, where xi and yi indicate the index of images from left-top
"""

import argparse
import os
import shutil
import platform
import sys
from pathlib import Path
from glob import glob
import time

import numpy as np  
import torch
import pandas as pd
import yaml

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLO root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode
from utils.mrcnn_nms import box_non_max_suppression

def get_subdirs(dir):
    subdirs = sorted([d for d in glob(os.path.join(dir, '*')) if os.path.isdir(d)])
    return(subdirs)

@smart_inference_mode()
def run(
        weights=ROOT / 'yolo.pt',  # model path or triton URL
        basedir=ROOT / 'data/images',  # path to site directory
        data=ROOT / 'data/coco.yaml',  # dataset.yaml path # TODO: load from train dir
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.1,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        line_thickness=3,  # bounding box thickness (pixels)
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride
        w = 2400,
        h = 2400,
        overlap_x = 400,
        overlap_y = 400,
):
    basedir = str(basedir)
    is_file = Path(basedir).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    assert is_file == False, 'designate path to base directory by --source'
    
    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # detection
    project = opt.basedir
    detection_csv_path = os.path.join(project, 'detections.csv')
    
    # generate blank dataframe for detection results
    columns = ['original_img', 'category_no', 'category', 'confidence', 'x1', 'y1', 'x2', 'y2']
    df = pd.DataFrame([], columns=columns)
    for col in ['original_img', 'category']:
        df[col] = df[col].astype(str)
    index_cnt = 0
    
    # Dataloader
    bs = 1  # batch_size
    dataset = LoadImages(basedir, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
    
    # Run inference
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    seen, dt = 0, (Profile(), Profile(), Profile())
    
    # non maximum suppression in absolute coordinate
    abs_boxes, scores, box_info_list = [], [], []

    for path, im, im0s, vid_cap, s in dataset:
        with dt[0]:
            im = torch.from_numpy(im).to(model.device)
            im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
            im /= 255  # 0 - 255 to 0.0 - 1.0
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim

        # Inference
        with dt[1]:
            pred = model(im, augment=augment, visualize=False)

        # NMS
        with dt[2]:
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            p, im0, frame = Path(path), im0s.copy(), getattr(dataset, 'frame', 0)

            s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0.copy()
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            
            img_name = p.name
            yi, xi = map(int, img_name[:-4].split('_'))
            Y = (h - overlap_y) * yi
            X = (w - overlap_x) * xi

            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, 5].unique():
                    n = (det[:, 5] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    x1, y1, x2, y2 = [int(num) for num in xyxy]
                    abs_boxes.append([y1 + Y, x1 + X, y2 + Y + 1, x2 + X + 1])
                    scores.append(float(conf))
                    # savename =  f"{img_name_base}_{Y + max(y1 - pad, 0):0=5}_{X + max(x1 - pad, 0):0=5}.jpg"
                    class_num = int(cls)
                    # cropped = save_one_box(
                    #     xyxy, 
                    #     imc,
                    #     pad=pad,
                    #     save=False,
                    #     BGR=True,
                    #     )
                    box_info_list.append({
                        'original_img':img_name,
                        'class_num':class_num,
                        'xyxy': [x1, y1, x2, y2],
                        # 'savename':savename,
                        # 'cropped':cropped,
                        })      

        # Print time (inference-only)
        # LOGGER.info(f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")

    # non maximum suppression under absolute coordinates
    if len(scores) >= 1:
        pick = box_non_max_suppression(np.array(abs_boxes), np.array(scores), iou_thres)
    else:
        pick = np.array([], dtype=np.int32)
    print(f"{len(scores) - len(pick)} duplications out of {len(scores)} detections were removed by absolute-NMS")
    
    # write results and save image
    for p in sorted(pick):
        box_info = box_info_list[p]
        df.loc[index_cnt, 'original_img'] = box_info['original_img']
        df.loc[index_cnt, 'category_no'] = box_info['class_num']
        df.loc[index_cnt, 'category'] = names[box_info['class_num']]
        df.loc[index_cnt, 'confidence'] = round(scores[p], 4)
        df.loc[index_cnt, ['x1', 'y1', 'x2', 'y2']] = box_info['xyxy']
        index_cnt += 1

    # Print results
    t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)

    # save csv
    for col in ['category_no', 'x1', 'y1', 'x2', 'y2']:
        df[col] = df[col].astype(int)
    df.to_csv(detection_csv_path)
    print(f"saved: {detection_csv_path}\n")
            

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf_thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou_thres', type=float, default=0.1, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    parser.add_argument('--vid-stride', type=int, default=1, help='video frame-rate stride')
    parser.add_argument('--basedir', type=str, default=ROOT / 'data/images', help='path to the base of image directories')
    opt = parser.parse_args()
    return opt

def add_info(opt):    
    # load start.txt
    with open(os.path.join(opt.basedir, 'start.txt')) as f:
        wh, overlap, model_name = f.read().splitlines()
    w, h = map(int, wh.split(','))
    overlap_x, overlap_y = map(int, overlap.split(','))
    opt.data = os.path.join(opt.basedir, 'data.yaml')
    opt.weights = f"./runs/train/{model_name}/weights/best.pt"
    assert os.path.exists(opt.weights), f"path not exists, please check model name: {model_name}"
    opt.w = w
    opt.h = h
    opt.overlap_x = overlap_x
    opt.overlap_y = overlap_y
    # load opt.yaml for getting imgsz
    with open(f"./runs/train/{model_name}/opt.yaml") as f:
        imgsz = yaml.safe_load(f)['imgsz']
    opt.imgsz = (imgsz, imgsz)
    print_args(vars(opt))
    return opt

def main(opt):
    check_requirements(exclude=('tensorboard', 'thop'))
    run(**vars(opt))

if __name__ == "__main__":
    opt = parse_opt()
    assert os.path.exists(opt.basedir), f"path not exists: {opt.basedir}"
    triger_path = os.path.join(opt.basedir, 'start.txt')
    while True:
        if os.path.exists(triger_path):
            LOGGER.info('process start!')
            opt = add_info(opt)
            main(opt)
            break
        else:
            LOGGER.info('waiting triger')
            time.sleep(5)
