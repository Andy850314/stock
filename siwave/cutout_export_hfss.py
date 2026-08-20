# -*- coding: utf-8 -*-
"""
SIwave 自動剪裁 (cutout) + 匯出 HFSS project

用 PyEDB 直接操作 EDB 資料庫，不模擬鍵盤、不依賴視窗焦點與選單助憶鍵。
可在無介面 (headless) 環境批次執行。

安裝:
    pip install pyedb
    # 舊版環境可改用:  pip install pyaedt   然後  from pyaedt import Edb

執行前請先在 SIwave 存檔並關閉該專案，避免 EDB 被鎖住。
"""

import os

try:
    from pyedb import Edb
except ImportError:                       # pyaedt < 0.9 的舊路徑
    from pyaedt import Edb


# ----------------------------------------------------------------------
# 使用者設定
# ----------------------------------------------------------------------
AEDB_PATH   = r"D:\260317\board.aedb"     # SIwave 專案的 .aedb 資料夾
EDB_VERSION = "2024.1"                    # 對應你安裝的 AEDT 版本

SIGNAL_NETS    = ["DSI1_BGA"]             # 要保留的訊號網路
REFERENCE_NETS = ["GND"]                  # 參考 (地) 網路

# 剪裁範圍。二選一:
#   (a) RECT_LAYER 設為你畫矩形所在的 layer 名稱 -> 自動抓那個矩形的範圍
#   (b) RECT_LAYER = None，改在 MANUAL_EXTENT 直接寫四個角座標
RECT_LAYER    = "OUTLINE"
MANUAL_EXTENT = [[0.0, 0.0], [10.0, 0.0], [10.0, 8.0], [0.0, 8.0]]
EXTENT_UNITS  = "mm"

CUTOUT_AEDB = r"D:\260317\auto_cutout.aedb"
HFSS_OUTPUT = r"D:\260317\auto"           # HFSS project 輸出資料夾


# ----------------------------------------------------------------------
def find_drawn_rectangle(edb, layer_name):
    """在指定 layer 上找出你手畫的矩形/多邊形，回傳角點座標 (公尺)。

    若該 layer 上有多個圖形，取面積最大的那個。
    """
    candidates = []
    for prim in edb.modeler.primitives:
        if prim.layer_name != layer_name:
            continue
        if prim.is_void:
            continue
        candidates.append(prim)

    if not candidates:
        raise RuntimeError(
            "在 layer '%s' 上找不到任何圖形。請確認 layer 名稱，"
            "或改用 MANUAL_EXTENT 手動指定座標。" % layer_name
        )

    def area_of(p):
        x0, y0, x1, y1 = p.bbox
        return abs(x1 - x0) * abs(y1 - y0)

    rect = max(candidates, key=area_of)
    x0, y0, x1, y1 = rect.bbox
    print("找到剪裁矩形: (%.6g, %.6g) -> (%.6g, %.6g) m" % (x0, y0, x1, y1))
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def main():
    if not os.path.isdir(AEDB_PATH):
        raise RuntimeError("找不到 EDB: %s" % AEDB_PATH)

    edb = Edb(edbpath=AEDB_PATH, edbversion=EDB_VERSION)
    try:
        # ---- 步驟 1: 決定剪裁範圍 ----
        if RECT_LAYER:
            extent = find_drawn_rectangle(edb, RECT_LAYER)
            units = "meter"
        else:
            extent = MANUAL_EXTENT
            units = EXTENT_UNITS

        # ---- 步驟 2: 執行 cutout ----
        # open_cutout_at_end=True -> 後續操作直接作用在剪裁後的 EDB 上
        ok = edb.cutout(
            signal_list=SIGNAL_NETS,
            reference_list=REFERENCE_NETS,
            custom_extent=extent,
            custom_extent_units=units,
            output_aedb_path=CUTOUT_AEDB,
            open_cutout_at_end=True,
            use_pyaedt_cutout=True,
            number_of_threads=4,
            remove_single_pin_components=True,
        )
        if not ok:
            raise RuntimeError("cutout 失敗，請檢查 net 名稱與剪裁範圍是否有重疊。")
        print("剪裁完成: %s" % CUTOUT_AEDB)

        # ---- 步驟 3: 匯出 HFSS project ----
        # 需要本機已安裝 SIwave (內部呼叫 siwave_ng 做轉檔)
        aedt_file = edb.export_hfss(HFSS_OUTPUT)
        if not aedt_file:
            raise RuntimeError("export_hfss 沒有產生檔案，請確認 SIwave 已安裝。")
        print("HFSS project 已輸出: %s" % aedt_file)

    finally:
        edb.close_edb()


if __name__ == "__main__":
    main()
