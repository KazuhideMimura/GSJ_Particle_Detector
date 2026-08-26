import yaml
import argparse
import os
import sys

from pathlib import Path
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLO root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative


def main(path_to_dataset, name0='', name1='', name2='', name3='', name4='', 
         name5='', name6='', name7='', name8='', name9='', name10='',
         lr0=0.01, flipud = 0.0, fliplr = 0.5):
    # data_from_gui.yaml
    # check input
    assert os.path.exists(path_to_dataset), f"path not exists: {path_to_dataset}"
    for subset in ['train', 'val']:
        assert os.path.exists(os.path.join(path_to_dataset, subset)), f"subdirectory {subset} is required under {path_to_dataset}"
    if os.path.exists(os.path.join(path_to_dataset, 'test')):
        testdir = 'test'
    else:
        testdir = 'val'
    # class names
    names = {}
    for i, name in enumerate([name0, name1, name2, name3, name4, name5, name6, name7, name8, name9]):
        if name != '':
            names[i] = name
    nc = len(names)
    data = {'path': path_to_dataset,
            'train': 'train',
            'val': 'val',
            'test': testdir,
            'nc': nc,
            'names': names}
    with open('data/data_from_gui.yaml', 'w', encoding='utf-8')as f:
       yaml.dump(data, f, default_flow_style=False)
    print("saved: data/data_from_gui.yaml")
    
    # hyperparameter
    # base: hyp.scratch-high.yaml
    hyp = {'lr0': lr0,
           'lrf': 0.01,
           'momentum': 0.937,
           'weight_decay': 0.0005,
           'warmup_epochs': 3.0,
           'warmup_momentum': 0.8,
           'warmup_bias_lr': 0.1,
           'box': 7.5,
           'cls': 0.5,
           'cls_pw': 1.0,
           'obj': 0.7,
           'obj_pw': 1.0,
           'dfl': 1.5,
           'iou_t': 0.2,
           'anchor_t': 5.0,
           'fl_gamma': 0.0,
           'hsv_h': 0.015,
           'hsv_s': 0.7,
           'hsv_v': 0.4,
           'degrees': 0.0,
           'translate': 0.1,
           'scale': 0.9,
           'shear': 0.0,
           'perspective': 0.0,
           'flipud': flipud,
           'fliplr': fliplr,
           'mosaic': 1.0,
           'mixup': 0.15,
           'copy_paste': 0.3
           }
    with open('data/hyps/hyp_from_gui.yaml', 'w', encoding='utf-8')as f:
        yaml.dump(hyp, f, default_flow_style=False)
    print('saved: data/hyps/hyp_from_gui.yaml')

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path_to_dataset', type = str, help='path to dataset directory')
    parser.add_argument('--name0', type = str, default='', help='name of class 0')
    parser.add_argument('--name1', type = str, default='', help='name of class 1')
    parser.add_argument('--name2', type = str, default='', help='name of class 2')
    parser.add_argument('--name3', type = str, default='', help='name of class 3')
    parser.add_argument('--name4', type = str, default='', help='name of class 4')
    parser.add_argument('--name5', type = str, default='', help='name of class 5')
    parser.add_argument('--name6', type = str, default='', help='name of class 6')
    parser.add_argument('--name7', type = str, default='', help='name of class 7')
    parser.add_argument('--name8', type = str, default='', help='name of class 8')
    parser.add_argument('--name9', type = str, default='', help='name of class 9')
    parser.add_argument('--lr0', type=float, default=0.01, help='initial learning rate')
    parser.add_argument('--flipud', type=float, default=0.0, help='likelyhood to randomly flip images upside down while training')
    parser.add_argument('--fliplr', type=float, default=0.5, help='likelyhood to randomly flip images (left/right) while training')
    opt = parser.parse_args()
    return opt

if __name__ == "__main__":
    opt = parse_opt()
    main(**vars(opt))
