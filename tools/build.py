"""Builds the mod from the installed game's own menu file.

python tools/build.py --ffdec path/to/ffdec.jar --w3edit path/to/w3edit.exe --variant reset
"""

import argparse
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

MENU = 'gameplay\\gui_new\\swf\\mainmenu\\panel_ingamemenu.redswf'
CLASS = 'red.game.witcher3.menus.mainmenu.GammaSettingModule'
# panel_ingamemenu.redswf from game version 5.00c
KNOWN_SHA256 = '49b6f09c5b4545aa87398cd6decd983abf92d1944e3b9bc23653a6fdb2bc1a34'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'tools', 'work')
# output folder per variant
VARIANTS = {'reset': 'Reset', 'value': 'Value', 'transparent': 'Transparent'}

PUBLIC = 'QName(PackageNamespace(""),"%s")'

# reset button id in the menu's input feedback bar
BUTTON_ID = 70


def feedback_call(label, call):
    return '\n'.join([
        'getlocal0',
        'getproperty ' + PUBLIC % 'parent',
        'iffalse ' + label,
        'pushstring "mcInputFeedbackModule"',
        'getlocal0',
        'getproperty ' + PUBLIC % 'parent',
        'in',
        'iffalse ' + label,
        'getlocal0',
        'getproperty ' + PUBLIC % 'parent',
        'getproperty ' + PUBLIC % 'mcInputFeedbackModule',
    ] + call + [label + ':'])


SHOW = feedback_call('ofs9101', [
    'pushbyte %d' % BUTTON_ID,
    'getlex QName(PackageNamespace("scaleform.clik.constants"),"NavigationCode")',
    'getproperty ' + PUBLIC % 'GAMEPAD_Y',
    'pushbyte 82',
    'pushstring "[[menu_option_reset_to_default]]"',
    'pushtrue',
    'callpropvoid ' + PUBLIC % 'appendButton' + ', 5',
])

HIDE = feedback_call('ofs9001', [
    'pushbyte %d' % BUTTON_ID,
    'pushtrue',
    'callpropvoid ' + PUBLIC % 'removeButton' + ', 2',
])

TEXT_FIELD = 'QName(PackageNamespace("flash.text"),"TextField")'
SHADOW = 'QName(PackageNamespace("flash.filters"),"DropShadowFilter")'


def value_code(field, rect, white):
    """Creates the value label once, then refreshes its text and position."""
    style = []
    color = []
    if white:
        color = [
            'getlocal %d' % field,
            'pushint 16777215',
            'setproperty ' + PUBLIC % 'textColor',
        ]
        style = [
            'getlocal %d' % field,
            'findpropstrict ' + SHADOW,
            'pushbyte 2',
            'pushbyte 45',
            'pushbyte 0',
            'pushdouble 0.9',
            'pushbyte 4',
            'pushbyte 4',
            'constructprop ' + SHADOW + ', 6',
            'newarray 1',
            'setproperty ' + PUBLIC % 'filters',
        ]
    return '\n'.join([
        'getlocal0',
        'pushstring "mcGammaValue"',
        'callproperty ' + PUBLIC % 'getChildByName' + ', 1',
        'setlocal %d' % field,
        'getlocal %d' % field,
        'iftrue ofs9401',
        'findpropstrict ' + TEXT_FIELD,
        'constructprop ' + TEXT_FIELD + ', 0',
        'setlocal %d' % field,
        'getlocal %d' % field,
        'pushstring "mcGammaValue"',
        'setproperty ' + PUBLIC % 'name',
        'getlocal %d' % field,
        'getlocal0',
        'getproperty ' + PUBLIC % 'txtTitle',
        'getproperty ' + PUBLIC % 'embedFonts',
        'setproperty ' + PUBLIC % 'embedFonts',
        'getlocal %d' % field,
        'getlocal0',
        'getproperty ' + PUBLIC % 'txtTitle',
        'callproperty ' + PUBLIC % 'getTextFormat' + ', 0',
        'setproperty ' + PUBLIC % 'defaultTextFormat',
        'getlocal %d' % field,
        'pushstring "left"',
        'setproperty ' + PUBLIC % 'autoSize',
        'getlocal %d' % field,
        'pushfalse',
        'setproperty ' + PUBLIC % 'selectable',
        'getlocal %d' % field,
        'pushfalse',
        'setproperty ' + PUBLIC % 'mouseEnabled',
    ] + style + [
        'getlocal0',
        'getlocal %d' % field,
        'callpropvoid ' + PUBLIC % 'addChild' + ', 1',
        'ofs9401:',
        'getlocal %d' % field,
        'getlocal0',
        'getproperty ' + PUBLIC % 'mcSlider',
        'getproperty ' + PUBLIC % 'value',
        'pushbyte 2',
        'callproperty ' + PUBLIC % 'toFixed' + ', 1',
        'setproperty ' + PUBLIC % 'text',
    ] + color + [
        'getlocal0',
        'getproperty ' + PUBLIC % 'mcSlider',
        'getproperty ' + PUBLIC % 'track',
        'getlocal0',
        'callproperty ' + PUBLIC % 'getBounds' + ', 1',
        'setlocal %d' % rect,
        'getlocal %d' % field,
        'getlocal %d' % rect,
        'getproperty ' + PUBLIC % 'x',
        'getlocal %d' % rect,
        'getproperty ' + PUBLIC % 'width',
        'add',
        'pushbyte 24',
        'add',
        'setproperty ' + PUBLIC % 'x',
        'getlocal0',
        'getproperty ' + PUBLIC % 'mcSlider',
        'getproperty ' + PUBLIC % 'thumb',
        'getlocal0',
        'callproperty ' + PUBLIC % 'getBounds' + ', 1',
        'setlocal %d' % rect,
        'getlocal %d' % field,
        'getlocal %d' % rect,
        'getproperty ' + PUBLIC % 'y',
        'getlocal %d' % rect,
        'getproperty ' + PUBLIC % 'height',
        'pushbyte 2',
        'divide',
        'add',
        'getlocal %d' % field,
        'getproperty ' + PUBLIC % 'height',
        'pushbyte 2',
        'divide',
        'subtract',
        'setproperty ' + PUBLIC % 'y',
    ])


# hide everything behind the slider
TRANSPARENT = '\n'.join([
    'getlocal0',
    'pushbyte 0',
    'callproperty ' + PUBLIC % 'getChildAt' + ', 1',
    'pushfalse',
    'setproperty ' + PUBLIC % 'visible',
    'getlocal0',
    'getproperty ' + PUBLIC % 'txtTitle',
    'pushfalse',
    'setproperty ' + PUBLIC % 'visible',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'iffalse ofs9501',
    'pushstring "mcBlackBackground"',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'in',
    'iffalse ofs9501',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'getproperty ' + PUBLIC % 'mcBlackBackground',
    'iffalse ofs9501',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'getproperty ' + PUBLIC % 'mcBlackBackground',
    'pushfalse',
    'setproperty ' + PUBLIC % 'backgroundForceVisible',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'getproperty ' + PUBLIC % 'mcBlackBackground',
    'pushfalse',
    'setproperty ' + PUBLIC % 'backgroundVisible',
    # a second show adds to the list instead of losing it
    'getlocal0',
    'getproperty ' + PUBLIC % 'modHidden',
    'dup',
    'iftrue ofs9506',
    'pop',
    'newarray 0',
    'ofs9506:',
    'setlocal 4',
    'pushnull',
    'setlocal 7',
    'pushstring "txtVersion"',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'in',
    'iffalse ofs9507',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'getproperty ' + PUBLIC % 'txtVersion',
    'setlocal 7',
    'ofs9507:',
    'pushbyte 0',
    'setlocal 5',
    'ofs9502:',
    'getlocal 5',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'getlocal0',
    'callproperty ' + PUBLIC % 'getChildIndex' + ', 1',
    'ifnlt ofs9504',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'getlocal 5',
    'callproperty ' + PUBLIC % 'getChildAt' + ', 1',
    'setlocal 6',
    'getlocal 6',
    'getproperty ' + PUBLIC % 'visible',
    'iffalse ofs9503',
    'getlocal 6',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'getproperty ' + PUBLIC % 'mcBlackBackground',
    'ifstricteq ofs9503',
    'getlocal 6',
    'getlocal 7',
    'ifstricteq ofs9503',
    'getlocal 6',
    'pushfalse',
    'setproperty ' + PUBLIC % 'visible',
    'getlocal 4',
    'getlocal 6',
    'callpropvoid ' + PUBLIC % 'push' + ', 1',
    'ofs9503:',
    'inclocal_i 5',
    'jump ofs9502',
    'ofs9504:',
    # visible does not stick on the version text, blank it instead
    'getlocal 7',
    'iffalse ofs9505',
    'pushstring "modVersionText"',
    'getlocal0',
    'in',
    'iftrue ofs9505',
    'getlocal0',
    'getlocal 7',
    'getproperty ' + PUBLIC % 'text',
    'setproperty ' + PUBLIC % 'modVersionText',
    'getlocal 7',
    'pushstring ""',
    'setproperty ' + PUBLIC % 'text',
    'ofs9505:',
    'getlocal0',
    'getlocal 4',
    'setproperty ' + PUBLIC % 'modHidden',
    'ofs9501:',
])

# shows again what showWithData hid
RESTORE = '\n'.join([
    'getlocal0',
    'getproperty ' + PUBLIC % 'modHidden',
    'iffalse ofs9603',
    'pushbyte 0',
    'setlocal 1',
    'ofs9601:',
    'getlocal 1',
    'getlocal0',
    'getproperty ' + PUBLIC % 'modHidden',
    'getproperty ' + PUBLIC % 'length',
    'ifnlt ofs9602',
    'getlocal0',
    'getproperty ' + PUBLIC % 'modHidden',
    'getlocal 1',
    'getproperty MultinameL([PackageNamespace("")])',
    'pushtrue',
    'setproperty ' + PUBLIC % 'visible',
    'inclocal_i 1',
    'jump ofs9601',
    'ofs9602:',
    'getlocal0',
    'pushnull',
    'setproperty ' + PUBLIC % 'modHidden',
    'ofs9603:',
    'pushstring "modVersionText"',
    'getlocal0',
    'in',
    'iffalse ofs9604',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'iffalse ofs9604',
    'pushstring "txtVersion"',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'in',
    'iffalse ofs9604',
    'getlocal0',
    'getproperty ' + PUBLIC % 'parent',
    'getproperty ' + PUBLIC % 'txtVersion',
    'getlocal0',
    'getproperty ' + PUBLIC % 'modVersionText',
    'setproperty ' + PUBLIC % 'text',
    'getlocal0',
    'deleteproperty ' + PUBLIC % 'modVersionText',
    'pop',
    'ofs9604:',
])


def bar_guard(label):
    return [
        'getlocal0',
        'getproperty ' + PUBLIC % 'parent',
        'iffalse ' + label,
        'pushstring "mcInputFeedbackModule"',
        'getlocal0',
        'getproperty ' + PUBLIC % 'parent',
        'in',
        'iffalse ' + label,
    ]


BAR = 'getlocal0\ngetproperty ' + PUBLIC % 'parent' + '\ngetproperty ' + PUBLIC % 'mcInputFeedbackModule'

# keep the prompt bar background hidden, as vanilla does here
BAR_OFF = '\n'.join(bar_guard('ofs9111') + [
    'getlocal0',
    BAR,
    'getproperty ' + PUBLIC % 'showBackground',
    'setproperty ' + PUBLIC % 'modBarBackground',
    BAR,
    'pushfalse',
    'setproperty ' + PUBLIC % 'showBackground',
    'ofs9111:',
])

BAR_RESTORE = '\n'.join(bar_guard('ofs9011') + [
    'pushstring "modBarBackground"',
    'getlocal0',
    'in',
    'iffalse ofs9011',
    BAR,
    'getlocal0',
    'getproperty ' + PUBLIC % 'modBarBackground',
    'setproperty ' + PUBLIC % 'showBackground',
    'getlocal0',
    'deleteproperty ' + PUBLIC % 'modBarBackground',
    'pop',
    'ofs9011:',
])


# R or gamepad Y sets the slider to 1, the vanilla default
INPUT = '\n'.join([
    'getlocal2',
    'getproperty ' + PUBLIC % 'value',
    'pushstring "keyUp"',
    'ifne ofs9201',
    'getlocal2',
    'getproperty ' + PUBLIC % 'code',
    'pushbyte 82',
    'ifeq ofs9202',
    'getlocal2',
    'getproperty ' + PUBLIC % 'navEquivalent',
    'pushstring "gamepad_Y"',
    'ifne ofs9201',
    'ofs9202:',
    'getlocal0',
    'getproperty ' + PUBLIC % 'mcSlider',
    'iffalse ofs9201',
    'getlocal0',
    'getproperty {data}',
    'iffalse ofs9201',
    'getlocal0',
    'getproperty ' + PUBLIC % 'mcSlider',
    'pushbyte 1',
    'setproperty ' + PUBLIC % 'value',
    'getlocal0',
    'pushnull',
    'callpropvoid {changed}, 1',
    'getlocal1',
    'pushtrue',
    'setproperty ' + PUBLIC % 'handled',
    'ofs9201:',
])


def fail(message):
    sys.exit('error: ' + message)


def read_bundle_file(bundle_path, name):
    with open(bundle_path, 'rb') as f:
        header = f.read(32)
        if header[:8] != b'POTATO70':
            fail('not a bundle: ' + bundle_path)
        table = f.read(struct.unpack('<I', header[16:20])[0])
        for i in range(0, len(table) - 303, 304):
            entry = table[i:i + 304]
            if entry[:256].split(b'\0')[0].decode('latin1') != name:
                continue
            offset, _, size, zsize, _, comp = struct.unpack('<6I', entry[272:296])
            f.seek(offset)
            data = f.read(zsize)
            if comp == 1:
                data = zlib.decompress(data)
            elif comp != 0:
                fail('unsupported compression %d' % comp)
            if len(data) != size:
                fail('size mismatch for ' + name)
            return data
    return None


def find_cfx(redswf):
    tables = [struct.unpack('<III', redswf[40 + i * 12:52 + i * 12]) for i in range(10)]
    eoff, ecnt, _ = tables[4]
    chunk = struct.unpack('<HHIIIII', redswf[eoff:eoff + 24])
    start, size = chunk[4], chunk[3]
    pos = redswf.find(b'CFX', start, start + size)
    if pos < 0:
        fail('no CFX data in the menu file')
    return pos, struct.unpack('<I', redswf[pos - 4:pos])[0]


def to_gfx(redswf):
    pos, length = find_cfx(redswf)
    version = redswf[pos + 3]
    declared = struct.unpack('<I', redswf[pos + 4:pos + 8])[0]
    body = zlib.decompress(redswf[pos + 8:pos + length])
    return b'GFX' + bytes([version]) + struct.pack('<I', declared) + body


def repack(redswf, gfx):
    out = bytearray(redswf)
    pos, length = find_cfx(redswf)
    cfx = gfx[:3].replace(b'GFX', b'CFX') + gfx[3:8] + zlib.compress(gfx[8:], 9)

    tables = [list(struct.unpack('<III', out[40 + i * 12:52 + i * 12])) for i in range(10)]
    eoff, ecnt, _ = tables[4]
    chunks = [list(struct.unpack('<HHIIIII', out[eoff + i * 24:eoff + i * 24 + 24])) for i in range(ecnt)]
    start, size = chunks[0][4], chunks[0][3]
    chunk = out[start:pos - 4] + struct.pack('<I', len(cfx)) + cfx + out[pos + length:start + size]
    delta = len(chunk) - size
    out = out[:start] + chunk + out[start + size:]

    chunks[0][3] = len(chunk)
    chunks[0][6] = zlib.crc32(bytes(chunk))
    for c in chunks[1:]:
        if c[4] > start:
            c[4] += delta
    for i, c in enumerate(chunks):
        out[eoff + i * 24:eoff + i * 24 + 24] = struct.pack('<HHIIIII', *c)
    tables[4][2] = zlib.crc32(bytes(out[eoff:eoff + ecnt * 24]))
    for i, t in enumerate(tables):
        out[40 + i * 12:52 + i * 12] = struct.pack('<III', *t)

    struct.pack_into('<II', out, 24, len(out), len(out))
    struct.pack_into('<I', out, 32, 0xDEADBEEF)
    struct.pack_into('<I', out, 32, zlib.crc32(bytes(out[:160])))
    return bytes(out)


class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def u8(self):
        self.pos += 1
        return self.data[self.pos - 1]

    def u30(self):
        value = shift = 0
        while True:
            byte = self.u8()
            value |= (byte & 0x7f) << shift
            if not byte & 0x80 or shift >= 28:
                return value
            shift += 7


def doabc(gfx):
    body = gfx[8:]
    rect = (5 + 4 * (body[0] >> 3) + 7) // 8
    pos = rect + 4
    while pos < len(body) - 1:
        code_len = struct.unpack('<H', body[pos:pos + 2])[0]
        pos += 2
        length = code_len & 63
        if length == 63:
            length = struct.unpack('<I', body[pos:pos + 4])[0]
            pos += 4
        if code_len >> 6 == 82:
            return body[pos:pos + length]
        pos += length
    fail('no ActionScript in the menu file')


def method_bodies(abc, class_name):
    """Maps method name to method body index for one class."""
    r = Reader(abc)
    r.pos = 4
    while abc[r.pos]:
        r.pos += 1
    r.pos += 5
    for _ in range(max(0, r.u30() - 1)):
        r.u30()
    for _ in range(max(0, r.u30() - 1)):
        r.u30()
    doubles = max(0, r.u30() - 1)
    r.pos += 8 * doubles
    strings = ['']
    for _ in range(max(0, r.u30() - 1)):
        length = r.u30()
        strings.append(abc[r.pos:r.pos + length].decode('utf8', 'replace'))
        r.pos += length
    for _ in range(max(0, r.u30() - 1)):
        r.u8()
        r.u30()
    for _ in range(max(0, r.u30() - 1)):
        for _ in range(r.u30()):
            r.u30()
    names = [None]
    for _ in range(max(0, r.u30() - 1)):
        kind = r.u8()
        if kind in (0x07, 0x0D):
            r.u30()
            names.append(r.u30())
        elif kind in (0x0F, 0x10):
            names.append(r.u30())
        elif kind in (0x11, 0x12):
            names.append(None)
        elif kind in (0x09, 0x0E):
            names.append(r.u30())
            r.u30()
        elif kind in (0x1B, 0x1C):
            r.u30()
            names.append(None)
        elif kind == 0x1D:
            names.append(None)
            r.u30()
            for _ in range(r.u30()):
                r.u30()
        else:
            fail('unknown multiname kind %x' % kind)

    def name(index):
        value = names[index] if index < len(names) else None
        return strings[value] if value is not None else ''

    for _ in range(r.u30()):
        count = r.u30()
        r.u30()
        for _ in range(count):
            r.u30()
        r.u30()
        flags = r.u8()
        if flags & 0x08:
            for _ in range(r.u30()):
                r.u30()
                r.u8()
        if flags & 0x80:
            for _ in range(count):
                r.u30()
    for _ in range(r.u30()):
        r.u30()
        for _ in range(2 * r.u30()):
            r.u30()

    def traits():
        found = {}
        for _ in range(r.u30()):
            trait_name = r.u30()
            kind = r.u8()
            if kind & 0x0f in (0, 6):
                r.u30()
                r.u30()
                if r.u30():
                    r.u8()
            elif kind & 0x0f in (1, 2, 3):
                r.u30()
                found[name(trait_name)] = r.u30()
            else:
                r.u30()
                r.u30()
            if kind & 0x40:
                for _ in range(r.u30()):
                    r.u30()
        return found

    class_count = r.u30()
    methods = None
    for _ in range(class_count):
        instance_name = r.u30()
        r.u30()
        if r.u8() & 0x08:
            r.u30()
        for _ in range(r.u30()):
            r.u30()
        r.u30()
        found = traits()
        if name(instance_name) == class_name:
            methods = found
    for _ in range(class_count):
        r.u30()
        traits()
    for _ in range(r.u30()):
        r.u30()
        traits()

    bodies = {}
    for index in range(r.u30()):
        method = r.u30()
        for _ in range(4):
            r.u30()
        code_length = r.u30()
        r.pos += code_length
        for _ in range(r.u30()):
            for _ in range(5):
                r.u30()
        traits()
        bodies[method] = index
    if methods is None:
        fail('class %s not found' % class_name)
    return {n: bodies[m] for n, m in methods.items() if m in bodies}


def method_block(pcode, name):
    found = re.search(r'trait method QName\([^)]*\),"%s"\)' % name, pcode)
    start = found.start() if found else -1
    begin = pcode.find('method\n', start + 13)
    end = pcode.find('end ; method', begin)
    if start < 0 or begin < 0 or end < 0:
        fail('method %s not found in P-code' % name)
    return pcode[begin:end + len('end ; method')]


def insert_before_last_return(block, code):
    pos = block.rfind('returnvoid')
    if pos < 0:
        fail('no returnvoid to anchor on')
    return block[:pos] + code + '\n' + block[pos:]


def raise_localcount(block, value):
    current = int(re.search(r'localcount (\d+)', block).group(1))
    return re.sub(r'localcount \d+', 'localcount %d' % max(current, value), block, count=1)


def raise_maxstack(block, value):
    current = int(re.search(r'maxstack (\d+)', block).group(1))
    return re.sub(r'maxstack \d+', 'maxstack %d' % max(current, value), block, count=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', default=r'D:\SteamLibrary\steamapps\common\The Witcher 3')
    parser.add_argument('--ffdec', required=True)
    parser.add_argument('--w3edit', required=True)
    parser.add_argument('--variant', choices=VARIANTS, default='reset')
    args = parser.parse_args()

    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)

    redswf = read_bundle_file(os.path.join(args.game, 'content', 'content0', 'bundles', 'r4gui.bundle'), MENU)
    if redswf is None:
        fail('menu file not found in r4gui.bundle')
    digest = hashlib.sha256(redswf).hexdigest()
    if digest != KNOWN_SHA256:
        print('note: the game changed the menu file since 5.00c, patching the new one')
        print('      sha256 ' + digest)

    vanilla_gfx = os.path.join(WORK, 'vanilla.gfx')
    with open(vanilla_gfx, 'wb') as f:
        f.write(to_gfx(redswf))

    subprocess.run(['java', '-jar', args.ffdec, '-selectclass', CLASS, '-format', 'script:pcode',
                    '-export', 'script', os.path.join(WORK, 'pcode'), vanilla_gfx], check=True, capture_output=True)
    with open(os.path.join(WORK, 'pcode', 'scripts', *CLASS.split('.')) + '.pcode') as f:
        pcode = f.read()

    changed = re.search(r'(QName\([^)]*\),"OnSliderValueChanged"\))', pcode)
    data = re.search(r'getproperty (QName\(PrivateNamespace\([^)]*\),"_data"\))', pcode)
    if not changed or not data:
        fail('gamma module no longer matches the patch')

    show = method_block(pcode, 'showWithData')
    slider_changed = None
    if args.variant != 'reset':
        white = args.variant == 'transparent'
        if white:
            show = insert_before_last_return(show, TRANSPARENT)
        show = raise_localcount(insert_before_last_return(show, value_code(2, 3, white)), 8 if white else 4)
        slider_changed = method_block(pcode, 'OnSliderValueChanged')
        slider_changed = raise_localcount(insert_before_last_return(slider_changed, value_code(3, 4, white)), 5)
    show = insert_before_last_return(insert_before_last_return(show, SHOW), BAR_OFF)
    hide = insert_before_last_return(insert_before_last_return(method_block(pcode, 'hide'), HIDE), BAR_RESTORE)
    if args.variant == 'transparent':
        hide = raise_localcount(insert_before_last_return(hide, RESTORE), 2)
    navigate = method_block(pcode, 'handleInputNavigate')
    anchor = '"convertWASDCodeToNavEquivalent"), 1\n'
    if anchor not in navigate:
        fail('input handler no longer matches the patch')
    navigate = navigate.replace(anchor, anchor + INPUT.format(changed=changed.group(1), data=data.group(1)) + '\n', 1)

    bodies = method_bodies(doabc(to_gfx(redswf)), CLASS.split('.')[-1])
    replace = []
    methods = [('showWithData', show, 10 if slider_changed else 8), ('hide', hide, 6 if args.variant == 'transparent' else 4), ('handleInputNavigate', navigate, 4)]
    if slider_changed:
        methods.append(('OnSliderValueChanged', slider_changed, 10))
    for name, block, stack in methods:
        path = os.path.join(WORK, name + '.pcode')
        with open(path, 'w') as f:
            f.write(raise_maxstack(block, stack))
        replace += [CLASS, path, str(bodies[name])]

    patched_gfx = os.path.join(WORK, 'patched.gfx')
    subprocess.run(['java', '-jar', args.ffdec, '-replace', vanilla_gfx, patched_gfx] + replace,
                   check=True, capture_output=True)
    with open(patched_gfx, 'rb') as f:
        gfx = f.read()
    if b'menu_option_reset_to_default' not in gfx:
        fail('patch did not apply')

    cooked = os.path.join(WORK, 'cooked')
    menu_path = os.path.join(cooked, *MENU.split('\\'))
    os.makedirs(os.path.dirname(menu_path))
    with open(menu_path, 'wb') as f:
        f.write(repack(redswf, gfx))

    packed = os.path.join(WORK, 'modGammaReset')
    subprocess.run([args.w3edit, 'bundle', 'pack', cooked, packed, '--format', 'remastered',
                    '--compression', 'zlib'], check=True, capture_output=True)
    subprocess.run([args.w3edit, 'metadata', 'create', packed, packed, '--format', 'remastered'],
                   check=True, capture_output=True)
    fix_metadata(os.path.join(packed, 'content', 'metadata.store'))

    content = os.path.join(ROOT, VARIANTS[args.variant], 'Mods', 'modGammaReset', 'content')
    os.makedirs(content, exist_ok=True)
    for name in ('blob0.bundle', 'metadata.store'):
        shutil.copyfile(os.path.join(packed, 'content', name), os.path.join(content, name))
    print('built ' + content)


def read_vlq(data, pos):
    byte = data[pos]
    pos += 1
    value = byte & 0x3f
    shift = 6
    more = byte & 0x40
    while more:
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7f) << shift
        shift += 7
        more = byte & 0x80
    return value, pos


def fix_metadata(path):
    # w3edit puts compression in the buffer id field
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    size, pos = read_vlq(data, 16)
    count, pos = read_vlq(data, pos + size)
    for i in range(1, count):
        offset = pos + i * 32
        record = list(struct.unpack('<8I', data[offset:offset + 32]))
        if record[7]:
            continue
        record[5], record[6], record[7] = 0, 0, record[5]
        data[offset:offset + 32] = struct.pack('<8I', *record)
    with open(path, 'wb') as f:
        f.write(data)


if __name__ == '__main__':
    main()
