# Gamma Reset

A Witcher 3 Remastered mod that adds a "Reset to Default" button to the gamma
screen.

Remastered looks a bit washed out, so I kept trying different gamma values to
reduce the washed out look. When I wanted to go back to the default, there was
no way to tell if the slider was exactly in the middle, since the slider shows
no number. This should have been added by CD Projekt RED, so players can
adjust the gamma to counter the washed out look until the lighting and bloom
get tweaked.

The button sits in the bottom bar of the gamma screen, next to the other
prompts, and uses the game's own "Reset to Default" label, so it is translated
in every language. Press R on keyboard, Y on a controller, or click it. The
slider jumps back to the default and the new value is saved like any other
change.

## Versions

Each version has its own folder with a `Mods` folder inside. Install only one
of them.

`Reset` adds the "Reset to Default" button.

`Value` also shows the gamma value next to the slider, so you can see exactly
where it is and come back to a value you liked.

`Transparent` also hides the grey backdrop and the test image, so the game
itself shows behind the slider and you can judge the gamma on the real scene.
The value is shown in white so it stays readable.

## Installing

This mod is for Remastered (game version 5.0 and later) only. It does not work
on Next-Gen 4.04 or older versions. Copy the `Mods` folder of the version you
want into your Witcher 3 folder.

## Compatibility

The mod replaces the game's options menu file,
`panel_ingamemenu.redswf`, with a patched copy. Any other mod that replaces the
same file will conflict with it, and only one of them can load.

A game update that changes that file would be hidden by this mod until it is
rebuilt against the new version.

## Building

`tools/build.py` rebuilds the mod from the menu file of the installed game. It
needs Python 3, Java, [JPEXS FFDec](https://github.com/jindrapetrik/jpexs-decompiler)
and [w3edit](https://github.com/Systemcluster/w3edit).

```
python tools/build.py --ffdec path/to/ffdec.jar --w3edit path/to/w3edit.exe --variant reset
```

`--variant` is `reset`, `value` or `transparent`. The script prints a note when
the game's menu file differs from the one the mod was made for, then patches
whichever version is installed.

MIT licensed.
