# -*- coding: utf-8 -*-
"""
Bad Apple Pixel Replacer
- 원본 영상의 흑/백 픽셀을 사용자가 지정한 두 이미지로 치환하여 영상으로 렌더링한다.
- GUI: PySide6
- 처리: OpenCV(프레임 읽기/리사이즈/이진화) + Pillow(타일 합성) + imageio-ffmpeg(인코딩)
"""

import os
import sys
import traceback

import cv2
import numpy as np
from PIL import Image
import imageio

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QSlider, QVBoxLayout, QHBoxLayout, QGroupBox, QMessageBox,
    QProgressBar, QSpinBox, QToolButton, QComboBox
)

RESULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result")
OUTPUT_NAME = "output.mp4"

# ------------------------------------------------------------------
# 다국어 텍스트 테이블
# ------------------------------------------------------------------
TRANSLATIONS = {
    "ko": {
        "window_title": "Bad Apple Pixel Replacer",
        "language_label": "Language",
        "video_group": "원본 영상",
        "select_video_btn": "영상 선택",
        "select_video_dialog": "원본 영상 선택",
        "not_selected": "선택 안됨",
        "black_group": "검정 픽셀 대응 이미지",
        "select_image_btn": "이미지 선택",
        "select_black_dialog": "검정 대응 이미지 선택",
        "white_group": "흰색 픽셀 대응 이미지",
        "select_white_dialog": "흰색 대응 이미지 선택",
        "bg_group": "배경 (선택사항)",
        "bg_remove_btn": "제거",
        "select_bg_dialog": "배경 선택 (이미지/영상/GIF)",
        "bg_help": (
            "검정/흰색 이미지가 투명 배경(PNG 등)을 가진 경우,\n"
            "투명한 부분 뒤로 이 배경이 비쳐 보입니다.\n"
            "이미지(정지) 외에 영상(mp4 등)이나 GIF도 넣을 수 있으며,\n"
            "이 경우 원본 영상이 끝날 때까지 배경이 반복 재생됩니다.\n"
            "지정하지 않으면 기본값으로 흰색 배경이 사용됩니다."
        ),
        "fps_group": "FPS",
        "res_group": "해상도 (가로 셀 개수)",
        "quality_group": "픽셀 대응 이미지 품질",
        "quality_low": "낮음",
        "quality_mid": "중간 (권장)",
        "quality_high": "높음",
        "quality_help": (
            "검정/흰색 대응 이미지 한 칸이 몇 픽셀로 표현될지 결정합니다.\n"
            "낮음(32px) / 중간(64px, 권장) / 높음(96px)\n"
            "높을수록 각 이미지가 더 선명하게 보이지만,\n"
            "최종 영상 해상도와 렌더링 시간이 함께 늘어납니다."
        ),
        "render_btn": "렌더링",
        "status_rendering": "렌더링 중...",
        "status_done": "렌더링 완료",
        "status_error": "오류 발생",
        "warn_title": "확인 필요",
        "warn_no_video": "원본 영상을 선택하세요.",
        "warn_no_images": "검정/흰색 대응 이미지를 모두 선택하세요.",
        "done_title": "완료",
        "done_text": "렌더링 완료. 프로그램 폴더 내 result 폴더를 확인하세요.\n\n{path}",
        "open_folder_btn": "폴더 열기",
        "error_title": "오류",
        "error_no_video": "영상 파일을 열 수 없습니다.",
        "error_no_bg_gif": "GIF에서 프레임을 읽지 못했습니다.",
        "error_no_bg_video": "배경 영상을 열 수 없습니다.",
        "error_no_bg_video_frames": "배경 영상에서 프레임을 읽지 못했습니다.",
        "error_unsupported_bg": "지원하지 않는 배경 파일 형식입니다: {ext}",
    },
    "en": {
        "window_title": "Bad Apple Pixel Replacer",
        "language_label": "Language",
        "video_group": "Source Video",
        "select_video_btn": "Select Video",
        "select_video_dialog": "Select Source Video",
        "not_selected": "Not selected",
        "black_group": "Image for Black Pixels",
        "select_image_btn": "Select Image",
        "select_black_dialog": "Select Image for Black Pixels",
        "white_group": "Image for White Pixels",
        "select_white_dialog": "Select Image for White Pixels",
        "bg_group": "Background (Optional)",
        "bg_remove_btn": "Remove",
        "select_bg_dialog": "Select Background (Image/Video/GIF)",
        "bg_help": (
            "If the black/white images have a transparent background (PNG, etc.),\n"
            "this background will show through the transparent areas.\n"
            "You can use a video (mp4, etc.) or GIF in addition to a still image;\n"
            "in that case, the background will loop until the source video ends.\n"
            "If not set, a white background is used by default."
        ),
        "fps_group": "FPS",
        "res_group": "Resolution (Horizontal Cell Count)",
        "quality_group": "Pixel Image Quality",
        "quality_low": "Low",
        "quality_mid": "Medium (Recommended)",
        "quality_high": "High",
        "quality_help": (
            "Determines how many pixels each black/white image cell is rendered at.\n"
            "Low(32px) / Medium(64px, recommended) / High(96px)\n"
            "Higher values make each image sharper, but also increase\n"
            "the final video resolution and rendering time."
        ),
        "render_btn": "Render",
        "status_rendering": "Rendering...",
        "status_done": "Render complete",
        "status_error": "An error occurred",
        "warn_title": "Required Fields",
        "warn_no_video": "Please select a source video.",
        "warn_no_images": "Please select both black and white images.",
        "done_title": "Done",
        "done_text": "Render complete. Check the result folder in the program directory.\n\n{path}",
        "open_folder_btn": "Open Folder",
        "error_title": "Error",
        "error_no_video": "Could not open the video file.",
        "error_no_bg_gif": "Could not read frames from the GIF.",
        "error_no_bg_video": "Could not open the background video.",
        "error_no_bg_video_frames": "Could not read frames from the background video.",
        "error_unsupported_bg": "Unsupported background file format: {ext}",
    },
    "ja": {
        "window_title": "Bad Apple Pixel Replacer",
        "language_label": "Language",
        "video_group": "元動画",
        "select_video_btn": "動画を選択",
        "select_video_dialog": "元動画を選択",
        "not_selected": "未選択",
        "black_group": "黒ピクセル対応画像",
        "select_image_btn": "画像を選択",
        "select_black_dialog": "黒対応画像を選択",
        "white_group": "白ピクセル対応画像",
        "select_white_dialog": "白対応画像を選択",
        "bg_group": "背景 (任意)",
        "bg_remove_btn": "削除",
        "select_bg_dialog": "背景を選択 (画像/動画/GIF)",
        "bg_help": (
            "黒/白の画像が透明背景(PNGなど)を持つ場合、\n"
            "透明な部分の背後にこの背景が透けて見えます。\n"
            "静止画像のほか、動画(mp4など)やGIFも使用できます。\n"
            "その場合、元動画が終わるまで背景がループ再生されます。\n"
            "指定しない場合は、デフォルトで白背景が使用されます。"
        ),
        "fps_group": "FPS",
        "res_group": "解像度(横方向のセル数)",
        "quality_group": "ピクセル対応画像の品質",
        "quality_low": "低",
        "quality_mid": "中 (推奨)",
        "quality_high": "高",
        "quality_help": (
            "黒/白対応画像の1マスが何ピクセルで表現されるかを決定します。\n"
            "低(32px) / 中(64px、推奨) / 高(96px)\n"
            "数値が高いほど各画像は鮮明になりますが、\n"
            "最終的な動画解像度とレンダリング時間も増加します。"
        ),
        "render_btn": "レンダリング",
        "status_rendering": "レンダリング中...",
        "status_done": "レンダリング完了",
        "status_error": "エラーが発生しました",
        "warn_title": "入力エラー",
        "warn_no_video": "元動画を選択してください。",
        "warn_no_images": "黒/白対応画像の両方を選択してください。",
        "done_title": "完了",
        "done_text": "レンダリングが完了しました。プログラムフォルダ内のresultフォルダを確認してください。\n\n{path}",
        "open_folder_btn": "フォルダを開く",
        "error_title": "エラー",
        "error_no_video": "動画ファイルを開けませんでした。",
        "error_no_bg_gif": "GIFからフレームを読み込めませんでした。",
        "error_no_bg_video": "背景動画を開けませんでした。",
        "error_no_bg_video_frames": "背景動画からフレームを読み込めませんでした。",
        "error_unsupported_bg": "サポートされていない背景ファイル形式です: {ext}",
    },
}


def tr(lang: str, key: str, **kwargs) -> str:
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ko"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def load_tile_rgba(img_path: str, tile_size: int) -> np.ndarray:
    """
    이미지를 tile_size x tile_size RGBA 배열로 불러온다.
    알파 채널이 없는 이미지는 완전 불투명(255)으로 채워서 반환한다.
    배경 합성은 여기서 하지 않는다 — 배경은 전체 프레임 레이어로 별도 처리한다.
    """
    img = Image.open(img_path).convert("RGBA").resize((tile_size, tile_size), Image.LANCZOS)
    return np.array(img)  # (tile_size, tile_size, 4)


class BackgroundSource:
    """
    배경으로 쓸 정적 이미지 / 영상(mp4 등) / GIF를 통일된 방식으로 다룬다.
    get_frame(index, size)를 호출하면 해당 프레임을 (H, W, 3) RGB numpy 배열로,
    화면 전체 크기(size=(width, height))에 맞춰 리사이즈해서 반환한다.
    배경의 총 프레임 수보다 index가 크면 처음부터 반복(루프)한다.
    정적 이미지는 항상 같은 프레임을 반환한다.
    """
    IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
    VIDEO_EXTS = (".mp4", ".avi", ".mov", ".mkv")
    GIF_EXTS = (".gif",)

    def __init__(self, path: str, lang: str = "ko"):
        self.path = path
        ext = os.path.splitext(path)[1].lower()

        if ext in self.IMAGE_EXTS:
            self.kind = "image"
            self._static_frame = Image.open(path).convert("RGB")
            self.frame_count = 1

        elif ext in self.GIF_EXTS:
            self.kind = "gif"
            reader = imageio.get_reader(path)
            self._frames = []
            for f in reader:
                self._frames.append(Image.fromarray(f).convert("RGB"))
            reader.close()
            if not self._frames:
                raise ValueError(tr(lang, "error_no_bg_gif"))
            self.frame_count = len(self._frames)

        elif ext in self.VIDEO_EXTS:
            self.kind = "video"
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                raise ValueError(tr(lang, "error_no_bg_video"))
            self._frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self._frames.append(Image.fromarray(rgb))
            cap.release()
            if not self._frames:
                raise ValueError(tr(lang, "error_no_bg_video_frames"))
            self.frame_count = len(self._frames)

        else:
            raise ValueError(tr(lang, "error_unsupported_bg", ext=ext))

    def get_frame(self, index: int, size) -> np.ndarray:
        """size: (width, height). 전체 화면 크기로 리사이즈해서 반환한다."""
        if self.kind == "image":
            pil_frame = self._static_frame
        else:
            # 배경이 원본보다 짧으면 처음부터 반복(루프)
            pil_frame = self._frames[index % self.frame_count]
        return np.array(pil_frame.resize(size, Image.LANCZOS))


def build_frame(binary_grid: np.ndarray, black_tile_rgba: np.ndarray, white_tile_rgba: np.ndarray,
                background_frame: np.ndarray = None) -> np.ndarray:
    """
    binary_grid: (rows, cols) 크기의 0/1 배열. 0=검정, 1=흰색.
    black_tile_rgba / white_tile_rgba: (tile_h, tile_w, 4) 크기의 RGBA 타일 이미지.
    background_frame: (rows*tile_h, cols*tile_w, 3) 크기로 이미 리사이즈된 배경 프레임. None이면 흰색 배경.

    구조 (뒤 -> 앞):
      레이어 1: 배경 (전체 화면 크기로 한 장)
      레이어 2: 흑/백 그리드 픽셀 (해상도에 따라 타일 개수가 달라짐), 타일의 투명한 부분은 배경이 비침
    """
    rows, cols = binary_grid.shape
    tile_h, tile_w, _ = black_tile_rgba.shape
    out_h, out_w = rows * tile_h, cols * tile_w

    # grid를 타일 크기만큼 확대 → 각 픽셀 위치가 흑/백 중 어느 타일을 써야 하는지의 마스크
    cell_mask = np.repeat(np.repeat(binary_grid, tile_h, axis=0), tile_w, axis=1)  # (out_h, out_w)
    cell_mask = cell_mask[:, :, None]

    # 흑/백 타일을 전체 화면 크기로 반복 배치 (RGB + 알파 각각)
    black_rgb = np.tile(black_tile_rgba[:, :, :3], (rows, cols, 1))
    white_rgb = np.tile(white_tile_rgba[:, :, :3], (rows, cols, 1))
    black_alpha = np.tile(black_tile_rgba[:, :, 3:4], (rows, cols, 1))
    white_alpha = np.tile(white_tile_rgba[:, :, 3:4], (rows, cols, 1))

    pixel_rgb = np.where(cell_mask == 1, white_rgb, black_rgb).astype(np.float32)
    pixel_alpha = np.where(cell_mask == 1, white_alpha, black_alpha).astype(np.float32) / 255.0

    # 레이어 1: 배경 준비 (없으면 흰색)
    if background_frame is not None:
        bg = background_frame.astype(np.float32)
    else:
        bg = np.full((out_h, out_w, 3), 255.0, dtype=np.float32)

    # 알파 합성: 픽셀 레이어의 불투명한 만큼 픽셀 색을, 투명한 만큼 배경을 보여줌
    frame = pixel_rgb * pixel_alpha + bg * (1.0 - pixel_alpha)
    return frame.astype(np.uint8)


class RenderThread(QThread):
    progress = Signal(int, int)   # (현재 프레임, 전체 프레임)
    finished_ok = Signal(str)     # 결과 파일 경로
    failed = Signal(str)          # 에러 메시지

    def __init__(self, video_path, black_img_path, white_img_path, fps, cols, tile_size=32,
                 background_path=None, lang="ko"):
        super().__init__()
        self.video_path = video_path
        self.black_img_path = black_img_path
        self.white_img_path = white_img_path
        self.fps = fps
        self.cols = cols  # 가로 그리드 셀 개수 (세로는 원본 비율로 자동 계산)
        self.tile_size = tile_size  # 타일(픽셀 대응 이미지) 한 칸의 픽셀 크기 - 품질 설정
        self.background_path = background_path  # 선택사항: 투명 PNG 뒤에 깔릴 배경
        self.lang = lang  # 에러 메시지 등에 사용할 언어

    def run(self):
        try:
            os.makedirs(RESULT_DIR, exist_ok=True)
            output_path = os.path.join(RESULT_DIR, OUTPUT_NAME)

            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.failed.emit(tr(self.lang, "error_no_video"))
                return

            src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 세로 그리드 셀 개수를 원본 비율에 맞춰 계산
            rows = max(1, round(self.cols * src_h / src_w))

            # 타일 이미지 준비 (RGBA). 타일 한 칸의 픽셀 크기는 사용자가 선택한 품질(tile_size)로 결정된다.
            # 최종 해상도는 grid(cols x rows) x tile_size로 조절된다.
            # 배경 합성은 여기서 하지 않고, 프레임별로 build_frame에서 레이어로 처리한다.
            TILE_SIZE = self.tile_size
            black_tile_rgba = load_tile_rgba(self.black_img_path, TILE_SIZE)
            white_tile_rgba = load_tile_rgba(self.white_img_path, TILE_SIZE)

            out_h, out_w = rows * TILE_SIZE, self.cols * TILE_SIZE  # 최종 프레임(=배경) 크기

            background_source = None
            if self.background_path:
                background_source = BackgroundSource(self.background_path, lang=self.lang)

            background_is_animated = background_source is not None and background_source.frame_count > 1

            if not background_is_animated:
                # 정적 배경(또는 배경 없음)이면 전체 화면 크기로 한 번만 만들어 재사용
                static_bg_frame = (
                    background_source.get_frame(0, (out_w, out_h)) if background_source else None
                )

            # 프레임 스킵 비율 계산 (요청 fps가 원본보다 낮으면 프레임을 건너뜀)
            frame_interval = max(1.0, src_fps / self.fps) if self.fps > 0 else 1.0

            writer = imageio.get_writer(output_path, fps=self.fps, codec="libx264",
                                         quality=None, pixelformat="yuv420p",
                                         macro_block_size=None)

            frame_idx = 0
            next_take = 0.0
            written = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx >= next_take:
                    # 그레이스케일 변환 + 그리드 크기로 다운샘플(평균 풀링에 가까운 INTER_AREA)
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    small = cv2.resize(gray, (self.cols, rows), interpolation=cv2.INTER_AREA)

                    # 단순 고정 임계값 이진화 (문제 생기면 이후 조정)
                    _, binary = cv2.threshold(small, 127, 1, cv2.THRESH_BINARY)

                    if background_is_animated:
                        # 배경이 영상/GIF인 경우, 이번 출력 프레임(written)에 맞는 배경을
                        # 전체 화면 크기로 매번 새로 준비한다. 원본보다 배경이 짧으면 자동 반복된다.
                        bg_frame = background_source.get_frame(written, (out_w, out_h))
                    else:
                        bg_frame = static_bg_frame

                    out_frame = build_frame(binary, black_tile_rgba, white_tile_rgba, bg_frame)
                    writer.append_data(out_frame)

                    written += 1
                    next_take += frame_interval

                frame_idx += 1
                if frame_idx % 10 == 0 or frame_idx == total_frames:
                    self.progress.emit(frame_idx, total_frames)

            cap.release()
            writer.close()

            self.finished_ok.emit(output_path)

        except Exception as e:
            self.failed.emit(f"{e}\n{traceback.format_exc()}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.lang = "ko"

        self.video_path = None
        self.black_img_path = None
        self.white_img_path = None
        self.background_path = None

        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        # 우측 상단 언어 선택
        lang_row = QHBoxLayout()
        lang_row.addStretch()
        self.lang_caption = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("한국어", "ko")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("日本語", "ja")
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_row.addWidget(self.lang_caption)
        lang_row.addWidget(self.lang_combo)
        layout.addLayout(lang_row)

        # 원본 영상 선택
        self.video_group = QGroupBox()
        video_layout = QHBoxLayout()
        self.video_label = QLabel()
        self.video_btn = QPushButton()
        self.video_btn.clicked.connect(self.select_video)
        video_layout.addWidget(self.video_label)
        video_layout.addWidget(self.video_btn)
        self.video_group.setLayout(video_layout)
        layout.addWidget(self.video_group)

        # 검정 대응 이미지
        self.black_group = QGroupBox()
        black_layout = QHBoxLayout()
        self.black_label = QLabel()
        self.black_btn = QPushButton()
        self.black_btn.clicked.connect(self.select_black_img)
        black_layout.addWidget(self.black_label)
        black_layout.addWidget(self.black_btn)
        self.black_group.setLayout(black_layout)
        layout.addWidget(self.black_group)

        # 흰색 대응 이미지
        self.white_group = QGroupBox()
        white_layout = QHBoxLayout()
        self.white_label = QLabel()
        self.white_btn = QPushButton()
        self.white_btn.clicked.connect(self.select_white_img)
        white_layout.addWidget(self.white_label)
        white_layout.addWidget(self.white_btn)
        self.white_group.setLayout(white_layout)
        layout.addWidget(self.white_group)

        # 배경 (선택사항, 투명 PNG/영상/GIF)
        self.bg_group = QGroupBox()
        bg_layout = QHBoxLayout()
        self.bg_label = QLabel()
        self.bg_btn = QPushButton()
        self.bg_btn.clicked.connect(self.select_background_img)
        self.bg_clear_btn = QPushButton()
        self.bg_clear_btn.clicked.connect(self.clear_background_img)

        self.bg_help = QToolButton()
        self.bg_help.setText("?")

        bg_layout.addWidget(self.bg_label)
        bg_layout.addWidget(self.bg_btn)
        bg_layout.addWidget(self.bg_clear_btn)
        bg_layout.addWidget(self.bg_help)
        self.bg_group.setLayout(bg_layout)
        layout.addWidget(self.bg_group)

        # FPS 조절
        self.fps_group = QGroupBox()
        fps_layout = QHBoxLayout()
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(30)
        fps_layout.addWidget(self.fps_spin)
        self.fps_group.setLayout(fps_layout)
        layout.addWidget(self.fps_group)

        # 해상도(가로 그리드 셀 개수) 조절
        self.res_group = QGroupBox()
        res_layout = QVBoxLayout()
        self.res_slider = QSlider(Qt.Horizontal)
        self.res_slider.setRange(20, 200)
        self.res_slider.setValue(35)
        self.res_value_label = QLabel("35")
        self.res_slider.valueChanged.connect(
            lambda v: self.res_value_label.setText(str(v))
        )
        res_row = QHBoxLayout()
        res_row.addWidget(self.res_slider)
        res_row.addWidget(self.res_value_label)
        res_layout.addLayout(res_row)
        self.res_group.setLayout(res_layout)
        layout.addWidget(self.res_group)

        # 픽셀 대응 이미지 품질 (타일 한 칸의 픽셀 크기)
        self.quality_group = QGroupBox()
        quality_layout = QHBoxLayout()
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("", 32)
        self.quality_combo.addItem("", 64)
        self.quality_combo.addItem("", 96)
        self.quality_combo.setCurrentIndex(1)  # 기본값: 중간(64)

        self.quality_help = QToolButton()
        self.quality_help.setText("?")

        quality_layout.addWidget(self.quality_combo)
        quality_layout.addWidget(self.quality_help)
        self.quality_group.setLayout(quality_layout)
        layout.addWidget(self.quality_group)

        # 렌더링 버튼 + 진행률
        self.render_btn = QPushButton()
        self.render_btn.clicked.connect(self.start_render)
        layout.addWidget(self.render_btn)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.thread = None

        self.retranslate_ui()

    # ------------------------------------------------------------------
    # 언어 전환
    # ------------------------------------------------------------------
    def on_language_changed(self):
        self.lang = self.lang_combo.currentData()
        self.retranslate_ui()

    def retranslate_ui(self):
        L = self.lang

        self.setWindowTitle(tr(L, "window_title"))
        self.lang_caption.setText(tr(L, "language_label"))

        self.video_group.setTitle(tr(L, "video_group"))
        self.video_btn.setText(tr(L, "select_video_btn"))
        if not self.video_path:
            self.video_label.setText(tr(L, "not_selected"))

        self.black_group.setTitle(tr(L, "black_group"))
        self.black_btn.setText(tr(L, "select_image_btn"))
        if not self.black_img_path:
            self.black_label.setText(tr(L, "not_selected"))

        self.white_group.setTitle(tr(L, "white_group"))
        self.white_btn.setText(tr(L, "select_image_btn"))
        if not self.white_img_path:
            self.white_label.setText(tr(L, "not_selected"))

        self.bg_group.setTitle(tr(L, "bg_group"))
        self.bg_btn.setText(tr(L, "select_image_btn"))
        self.bg_clear_btn.setText(tr(L, "bg_remove_btn"))
        self.bg_help.setToolTip(tr(L, "bg_help"))
        if not self.background_path:
            self.bg_label.setText(tr(L, "not_selected"))

        self.fps_group.setTitle(tr(L, "fps_group"))
        self.res_group.setTitle(tr(L, "res_group"))

        self.quality_group.setTitle(tr(L, "quality_group"))
        self.quality_combo.setItemText(0, tr(L, "quality_low"))
        self.quality_combo.setItemText(1, tr(L, "quality_mid"))
        self.quality_combo.setItemText(2, tr(L, "quality_high"))
        self.quality_help.setToolTip(tr(L, "quality_help"))

        self.render_btn.setText(tr(L, "render_btn"))

    # ------------------------------------------------------------------
    # 파일 선택
    # ------------------------------------------------------------------
    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr(self.lang, "select_video_dialog"), "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if path:
            self.video_path = path
            self.video_label.setText(os.path.basename(path))

    def select_black_img(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr(self.lang, "select_black_dialog"), "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self.black_img_path = path
            self.black_label.setText(os.path.basename(path))

    def select_white_img(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr(self.lang, "select_white_dialog"), "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self.white_img_path = path
            self.white_label.setText(os.path.basename(path))

    def select_background_img(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr(self.lang, "select_bg_dialog"), "",
            "Background Files (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.mp4 *.avi *.mov *.mkv)"
        )
        if path:
            self.background_path = path
            self.bg_label.setText(os.path.basename(path))

    def clear_background_img(self):
        self.background_path = None
        self.bg_label.setText(tr(self.lang, "not_selected"))

    # ------------------------------------------------------------------
    # 렌더링
    # ------------------------------------------------------------------
    def start_render(self):
        L = self.lang
        if not self.video_path:
            QMessageBox.warning(self, tr(L, "warn_title"), tr(L, "warn_no_video"))
            return
        if not self.black_img_path or not self.white_img_path:
            QMessageBox.warning(self, tr(L, "warn_title"), tr(L, "warn_no_images"))
            return

        self.render_btn.setEnabled(False)
        self.status_label.setText(tr(L, "status_rendering"))
        self.progress_bar.setValue(0)

        fps = self.fps_spin.value()
        cols = self.res_slider.value()
        tile_size = self.quality_combo.currentData()

        self.thread = RenderThread(
            self.video_path, self.black_img_path, self.white_img_path, fps, cols,
            tile_size=tile_size, background_path=self.background_path, lang=L
        )
        self.thread.progress.connect(self.on_progress)
        self.thread.finished_ok.connect(self.on_finished)
        self.thread.failed.connect(self.on_failed)
        self.thread.start()

    def on_progress(self, current, total):
        if total > 0:
            self.progress_bar.setValue(int(current / total * 100))

    def on_finished(self, output_path):
        L = self.lang
        self.render_btn.setEnabled(True)
        self.status_label.setText(tr(L, "status_done"))
        self.progress_bar.setValue(100)

        msg = QMessageBox(self)
        msg.setWindowTitle(tr(L, "done_title"))
        msg.setText(tr(L, "done_text", path=output_path))
        open_btn = msg.addButton(tr(L, "open_folder_btn"), QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)
        msg.exec()

        if msg.clickedButton() == open_btn:
            self.open_result_folder()

    def on_failed(self, error_msg):
        L = self.lang
        self.render_btn.setEnabled(True)
        self.status_label.setText(tr(L, "status_error"))
        QMessageBox.critical(self, tr(L, "error_title"), error_msg)

    def open_result_folder(self):
        try:
            if sys.platform.startswith("win"):
                os.startfile(RESULT_DIR)
            elif sys.platform == "darwin":
                os.system(f'open "{RESULT_DIR}"')
            else:
                os.system(f'xdg-open "{RESULT_DIR}"')
        except Exception:
            # 폴더 열기가 안 되면 그냥 무시 (필수 기능 아님)
            pass


if __name__ == "__main__":
    os.makedirs(RESULT_DIR, exist_ok=True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
