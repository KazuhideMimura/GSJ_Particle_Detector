# GSJ Particle Detector
<a href="https://doi.org/10.5281/zenodo.22114711"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.22114711.svg" alt="DOI"></a>

## Citation
If you use this program, please cite it as below:
> Mimura, K., Itaki, T., & Miyakawa, A. (2026). GSJ Particle Detector (Version v1.0.4) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22114711

Please also consider citing the following paper for use of object detection in geological observations.

> Mimura, K., Nakamura, K., Yasukawa, K., Sibert, E. C., Ohta, J., Kitazawa, T., & Kato, Y. (2024). Applicability of object detection to microfossil research: Implications from deep learning models to detect microfossil fish teeth and denticles using YOLO‐v7. Earth and Space Science, 11(1), e2023EA003122. https://doi.org/10.1029/2023EA003122

## About
<B>GSJ Particle Detector</B> is an object detection application designed to detect and crop particles from geological images, especially microscopic images. Based on [YOLO-v9](https://github.com/WongKinYiu/yolov9), this package provides a simple graphical user interface to conduct training and inference of object detection models.

The application can also be integrated with other software systems and applications to automatically perform object detection by monitoring a specified folder and triggering the detection process when new data are detected.

<details>
<summary>日本語</summary>
<B>GSJ Particle Detector</B> は、地質試料画像、特に顕微鏡画像を対象として粒子を検出・切り出すための AI 物体検出アプリケーションです。[YOLO-v9](https://github.com/WongKinYiu/yolov9) のプログラムを核として、本ソフトウェアは物体検出モデルの学習および推論を行うためのシンプルなグラフィカルユーザーインターフェース（GUI）を提供します。

また、他のソフトウェアやアプリケーションと連携し、指定したフォルダを監視することで、新しいデータが検出された際に自動的に物体検出処理を実行することができます。
</details>

## Environment

This application is designed to be installed and used within a Python environment capable of running YOLOv9. Please create an environment for yolov9 using a environment manager, such as Miniconda.

<details>
<summary>日本語</summary>
本アプリケーションは、YOLOv9 を実行できる Python 環境にインストールして利用します。Miniconda 等で作成した環境での利用を想定しています。

事前に YOLOv9 の実行環境を構築し、YOLOv9 の実行に必要な依存パッケージをインストールしてください。
</details>

## Install

In a Python environment with YOLOv9 installed, run the following command:

`pip install --find-links=(designate the package directory)/ GSJParticleDetector`

## Setting up
For the first launch, run the following command:

```gsj_pd```

When the initial setup dialog appears, specify the location of the YOLOv9 folder (`YOLOv9_AIST_202XXXXX`) in the “YOLOv9 folder path” field.

You can also create a desktop shortcut. Once the shortcut has been created, the application can be launched by double-clicking the icon.

### Pretrained weights
Pretrained models are not included in this package. Download yolov9-s, yolov9-m, yolov9-c, and yolov9-e from the [official YOLOv9 repository](https://github.com/WongKinYiu/yolov9), and place the downloaded model files in the directory `YOLOv9_AIST_20260818/pretrained`.


## Main functions

The following operations can be performed through the graphical user interface (GUI):

- Run object detection on image datasets
- Manage trained object detection models
- Train and evaluate object detection models
- Perform test detection using trained models

For detailed operating instructions, please refer to the [User Manual](files_for_readme/Manual_v1_0_4_Jp.pdf) (currently available only in Japanese).

<details>
<summary>日本語</summary>
本アプリケーションでは、以下の操作を GUI 上で実行できます。

- 画像データに対する物体検出の実行
- 学習済み物体検出モデルの管理
- 物体検出モデルの学習および評価
- 学習済みモデルによる試験検出

詳細な操作方法については、[利用マニュアル](files_for_readme/Manual_v1_0_4_Jp.pdf) を参照してください。
</details>

## Log
- 2026.9.3: [v1.0.5](https://github.com/KazuhideMimura/GSJ_Particle_Detector/commit/caef731e35bf8a25d45ef72fb5ae876c5da05849) (bug fix)
- 2026.8.26: [v1.0.4](https://github.com/KazuhideMimura/GSJ_Particle_Detector/releases) (First published)

## Copyright
Copyright (c) 2026 National Institute of Advanced Industrial Science and Technology (AIST)
