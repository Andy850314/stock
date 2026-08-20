# SIwave 自動剪裁 + 匯出 HFSS

## cutout_export_hfss.py（建議使用）

用 PyEDB 直接操作 EDB 資料庫完成 cutout 與 HFSS 匯出，不需要模擬鍵盤、
不依賴視窗焦點或選單助憶鍵，可批次執行。

使用前修改檔案頂端的設定區：

| 變數 | 說明 |
| --- | --- |
| `AEDB_PATH` | SIwave 專案的 `.aedb` 資料夾路徑 |
| `EDB_VERSION` | 對應安裝的 AEDT 版本，如 `"2024.1"` |
| `SIGNAL_NETS` / `REFERENCE_NETS` | 要保留的訊號網路與參考網路 |
| `RECT_LAYER` | 手畫矩形所在的 layer 名稱；設為 `None` 則改用 `MANUAL_EXTENT` |
| `MANUAL_EXTENT` | 手動指定剪裁範圍的四個角座標 |
| `CUTOUT_AEDB` | 剪裁結果輸出路徑 |
| `HFSS_OUTPUT` | HFSS project 輸出資料夾 |

執行前請先在 SIwave 存檔並關閉專案，避免 EDB 被鎖住。

```
pip install pyedb
python siwave/cutout_export_hfss.py
```

`export_hfss` 需要本機已安裝 SIwave（內部呼叫 `siwave_ng` 轉檔）。

## sendkeys_fallback.py（最後手段）

只有在 PyEDB 完全不能用時才考慮。相較於單純的 SendKeys，它會明確把
SIwave 帶到前景、用 UI Automation 確認對話框真的出現、直接以
ValuePattern/InvokePattern 填欄位與按 OK，並在任一步失敗時立刻中止。

仍然依賴視窗標題與控制項名稱，換 SIwave 版本可能要調整
`EXPORT_DIALOG_TITLE` 與選單助憶鍵。

## 找出正確的 SIwave 腳本指令

若想留在 SIwave 內建 scripting，不要猜指令名稱：用
**Tools → Record Script** 手動操作一次 cutout 與 export，
錄下來的檔案就是該版本正確的 `oDoc.Scr*` 指令與參數。
