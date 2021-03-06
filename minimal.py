import sys
import os
import time

sys.path.append("lib")
sys.path.append("library.zip")
import pyauto
from Key import Key

class Binding:
    def __init__(self, key, ctrl=False, alt=False, shift=False):
        self.key = key
        self.ctrl = ctrl
        self.alt = alt
        self.shift = shift
    def __str__(self):
        return "Binding: key = {0.key}, ctrl = {0.ctrl}, alt = {0.alt}, shift = {0.shift}".format(self)

class InputManager:
    def __init__(self):
        # OS 内でモディファイアーが仮想的に押されたことになっているか
        self.os_mods = {
            Key.LEFT_CTRL: False,
            Key.LEFT_ALT: False,
            Key.LEFT_SHIFT: False
        }

    def _sync_modifiers(self, mods):
        for code in [Key.LEFT_CTRL, Key.LEFT_ALT, Key.LEFT_SHIFT]:
            if self.os_mods[code] != mods[code]:
                self.send_key(code, mods[code])

    def exec_binding_down(self, binding, up=True):
        #print(binding)
        #print("os_mods: ctrl = {ctrl}, alt = {alt}, shift = {shift}".format(ctrl=self.os_mods[Key.ctrl], alt=self.os_mods[Key.alt], shift=self.os_mods[Key.shift]))
        # モディファイアーの状態を保存して同期
        mods_copy = self.os_mods.copy()
        self._sync_modifiers({
            Key.LEFT_CTRL: binding.ctrl,
            Key.LEFT_ALT: binding.alt,
            Key.LEFT_SHIFT: binding.shift
        })
        # 通常キー押下を実行
        self.send_key(binding.key)
        # アップ
        if up:
            self.send_key(binding.key, False)
        # モディファイアーの状態を戻す
        self._sync_modifiers(mods_copy)

    def send_key(self, key, down=True):
        #print("send_key: {key} {down}".format(key=key, down=down))
        if down:
            pyauto.Input.send([pyauto.KeyDown(key)])
        else:
            pyauto.Input.send([pyauto.KeyUp(key)])
        if key in self.os_mods:
            self.os_mods[key] = down

    def reset(self):
        for key, status in self.os_mods.items():
            self.send_key(key, False)

class Controller:
    def __init__(self):
        self.manager = InputManager()

        # 現在モディファイアーが実際に押されているか
        self.mods = {
            Key.v_command: False,
            Key.v_control: False,
            Key.v_option: False,
            Key.v_shift: False
        }
        #  タスク切り替え（command-tab）中か
        self.task_switch = False
        # キー バインディング
        # モディファイアーの優先順位は command、ctrl、option、shift
        self.binding_map = {
            str(Key.OEM_102): [Binding(Key.OEM_102, False, False, True)],
            str(Key.INSERT): [Binding(Key.F12)],
            "command-" + str(Key.V): [Binding(Key.INSERT, False, False, True)],
            "command-" + str(Key.Q): [Binding(Key.F4, False, True)],
            "control-" + str(Key.SPACE): [Binding(Key.U, True)],
            "control-" + str(Key.A): [Binding(Key.HOME)],
            "control-" + str(Key.B): [Binding(Key.LEFT)],
            "control-" + str(Key.D): [Binding(Key.DELETE)],
            "control-" + str(Key.E): [Binding(Key.END)],
            "control-" + str(Key.F): [Binding(Key.RIGHT)],
            "control-" + str(Key.G): [Binding(Key.ESCAPE)],
            "control-" + str(Key.H): [Binding(Key.BACK)],
            "control-" + str(Key.I): [Binding(Key.TAB)],
            "control-" + str(Key.M): [Binding(Key.RETURN)],
            "control-" + str(Key.N): [Binding(Key.DOWN)],
            "control-" + str(Key.P): [Binding(Key.UP)],
            "control-" + str(Key.Q): [Binding(Key.PRIOR)],
            "control-" + str(Key.S): [Binding(Key.A, True)],
            "control-" + str(Key.W): [Binding(Key.NEXT)],
            "control-" + str(Key.OEM_PERIOD): [Binding(Key.END, True)],
            "control-" + str(Key.OEM_COMMA): [Binding(Key.HOME, True)],
            "command-control-" + str(Key.A): [Binding(Key.HOME, False, False, True)],
            "command-control-" + str(Key.B): [Binding(Key.LEFT, False, False, True)],
            "command-control-" + str(Key.E): [Binding(Key.END, False, False, True)],
            "command-control-" + str(Key.F): [Binding(Key.RIGHT, False, False, True)],
            "command-control-" + str(Key.N): [Binding(Key.DOWN, False, False, True)],
            "command-control-" + str(Key.P): [Binding(Key.UP, False, False, True)],
            "command-control-" + str(Key.D): [Binding(Key.DELETE, True)],
            "command-control-" + str(Key.H): [Binding(Key.BACK, True)],
            str(Key.HIRAGANA_KATAKANA): [Binding(Key.LEFT, False, True)],
            str(Key.NONCONVERT): [Binding(Key.W, True)],
        }

    def on_key_down(self, key, scan):
        #print("D: ", key)
        if key == Key.F4:
            self.exit()
        # モディファイアーの場合
        if key in self.mods:
            return self.on_mod_down(key)
        # Tab は特別処理
        if key == Key.TAB:
            return self.on_tab_down()
        # その他のキーの場合
        return self.on_normal_key_down(key)

    def on_mod_down(self, key):
        self.mods[key] = True
        if key != Key.v_control:
            self.manager.send_key(key)
        return True

    def on_normal_key_down(self, key):
        # バインディングを組み立て
        binding = ""
        if self.mods[Key.v_command]:
            binding += "command-"
        if self.mods[Key.v_control]:
            binding += "control-"
        if self.mods[Key.v_option]:
            binding += "option-"
        if self.mods[Key.v_shift]:
            binding += "shift-"
        binding += str(key)
        # バインディングを検索
        if binding in self.binding_map:
            bindings = self.binding_map[binding]
        else:
            bindings = [
                Binding(
                    key,
                    self.mods[Key.v_command] or self.mods[Key.v_control],
                    self.mods[Key.v_option],
                    self.mods[Key.v_shift]
                )
            ]
        for i in bindings:
            self.manager.exec_binding_down(i)
        return True

    def on_tab_down(self):
        # スペースキーが押されていなければそのまま通す
        if not self.mods[Key.v_command]:
            return self.on_normal_key_down(Key.TAB)
        if not self.task_switch:
            self.manager.send_key(Key.RIGHT_CTRL, False)
            self.manager.send_key(Key.LEFT_ALT)
            self.task_switch = True
        self.manager.send_key(Key.TAB)
        return True

    def on_key_up(self, key, scan):
        #print("U: ", key)
        # モディファイアーの場合
        if key in self.mods:
            return self.on_mod_up(key)
        return True

    def on_mod_up(self, key):
        if key == Key.v_command and self.mods[Key.v_command]:
            # タスク切り替え中なら alt を離す
            if self.task_switch:
                #print("task-switch end")
                self.manager.send_key(Key.LEFT_ALT, False)
                self.task_switch = False
        self.mods[key] = False
        self.manager.send_key(key, False)
        return True

    def exit(self):
        self.manager.reset()
        sys.exit(0)

controller = Controller()

hook = pyauto.Hook()
hook.keydown = controller.on_key_down
hook.keyup = controller.on_key_up

pyauto.messageLoop()
