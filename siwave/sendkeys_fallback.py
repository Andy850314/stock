# -*- coding: utf-8 -*-
"""
GUI 自動化的「最後手段」版本 —— 只有在 PyEDB 真的不能用時才考慮。

與原始 SendKeys 腳本相比修正了:
  1. 明確把 SIwave 主視窗帶到前景 (不再依賴滑鼠位置)
  2. 用 UI Automation 等待並「確認」對話框真的出現，而不是 sleep 猜時間
  3. 直接用 ValuePattern 填欄位、InvokePattern 按 OK，不靠 Enter 猜行為
  4. SendKeys 特殊字元跳脫
  5. 每個步驟失敗就立刻中止，不會繼續亂打按鍵

注意: 這個做法仍然依賴視窗標題與控制項名稱，換 SIwave 版本就可能要改。
      正解請看 cutout_export_hfss.py。
"""

import time
import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("UIAutomationClient")
clr.AddReference("UIAutomationTypes")
clr.AddReference("Microsoft.VisualBasic")

from System.Windows.Forms import SendKeys
from System.Windows.Automation import (
    AutomationElement,
    ControlType,
    InvokePattern,
    PropertyCondition,
    TreeScope,
    ValuePattern,
)
from System.Diagnostics import Process
from Microsoft.VisualBasic import Interaction


TARGET_PATH = r"D:\260317\auto"
EXPORT_DIALOG_TITLE = "Export HFSS"      # 依你的 SIwave 版本調整
SIWAVE_PROCESS_NAME = "siwave"


# ----------------------------------------------------------------------
def escape_sendkeys(text):
    """跳脫 SendKeys 的控制字元: + ^ % ~ ( ) { } [ ]"""
    out = []
    for ch in text:
        if ch in "+^%~(){}[]":
            out.append("{%s}" % ch)
        else:
            out.append(ch)
    return "".join(out)


def focus_siwave():
    """把 SIwave 主視窗帶到前景。找不到就丟例外，不繼續往下打按鍵。"""
    procs = [p for p in Process.GetProcessesByName(SIWAVE_PROCESS_NAME)
             if p.MainWindowHandle != 0]
    if not procs:
        raise RuntimeError("找不到執行中的 SIwave 主視窗。")
    Interaction.AppActivate(procs[0].Id)
    time.sleep(0.3)
    return procs[0]


def wait_for_window(title_substring, timeout=20.0, poll=0.25):
    """輪詢桌面上的頂層視窗，等到標題含指定字串的視窗出現為止。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        root = AutomationElement.RootElement
        windows = root.FindAll(
            TreeScope.Children,
            PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window),
        )
        for i in range(windows.Count):
            win = windows[i]
            name = win.Current.Name or ""
            if title_substring.lower() in name.lower():
                return win
        time.sleep(poll)
    raise RuntimeError(
        "等了 %.1f 秒仍未出現標題含 '%s' 的視窗。" % (timeout, title_substring)
    )


def find_child(window, control_type, name=None):
    cond = PropertyCondition(AutomationElement.ControlTypeProperty, control_type)
    elements = window.FindAll(TreeScope.Descendants, cond)
    for i in range(elements.Count):
        el = elements[i]
        if name is None or (el.Current.Name or "").strip().lower() == name.lower():
            return el
    return None


def set_edit_text(window, text):
    """填入對話框中第一個可編輯的文字欄位。"""
    edit = find_child(window, ControlType.Edit)
    if edit is None:
        raise RuntimeError("對話框中找不到文字輸入欄位。")
    pattern = edit.GetCurrentPattern(ValuePattern.Pattern)
    if pattern.Current.IsReadOnly:
        raise RuntimeError("文字欄位是唯讀的，無法填入路徑。")
    pattern.SetValue(text)


def click_button(window, button_name):
    btn = find_child(window, ControlType.Button, button_name)
    if btn is None:
        raise RuntimeError("對話框中找不到 '%s' 按鈕。" % button_name)
    btn.GetCurrentPattern(InvokePattern.Pattern).Invoke()


# ----------------------------------------------------------------------
def main():
    proc = focus_siwave()
    print("已將 SIwave (PID %d) 帶到前景。" % proc.Id)

    # 開啟 File 選單。助憶鍵因版本而異，若這裡沒反應請改用實際選單路徑。
    SendKeys.SendWait("%f")
    time.sleep(0.4)
    SendKeys.SendWait("e")
    time.sleep(0.4)
    SendKeys.SendWait("h")

    # 這裡才是關鍵: 確認對話框真的出現了，而不是 sleep 完就假設成功
    dialog = wait_for_window(EXPORT_DIALOG_TITLE, timeout=20.0)
    print("Export 對話框已出現: %s" % dialog.Current.Name)

    set_edit_text(dialog, TARGET_PATH)
    print("已填入路徑: %s" % TARGET_PATH)

    click_button(dialog, "OK")
    print("已按下 OK，開始匯出。")

    # 等對話框關閉，代表 SIwave 已接手處理
    deadline = time.time() + 600.0
    while time.time() < deadline:
        try:
            _ = dialog.Current.Name
        except Exception:
            print("對話框已關閉，匯出流程已交給 SIwave。")
            return
        time.sleep(1.0)
    raise RuntimeError("對話框超過 10 分鐘仍未關閉。")


if __name__ == "__main__":
    main()
