# bfb-blender

A toolset for blender allowing the import export of Zoo Tycoon 2 models and animations, as well as maps and particle systems (experimental!).

### Installation
- Click the `Clone or Download` button at the right, then `Download ZIP`.
- Extract the ZIP you just downloaded and pack the _contents_ of the `bfb-blender-master` folder into a new ZIP file.
- To install with the addon installer in Blender, click `File` > `User Preferences` > `Add-ons` > `Install Add-ons from File` and select your new ZIP file.

### How To Use
#### Importing Models
- `File` > `Import` > `Blue Fang Model (.bfb)`. Import from a Z2F-like file structure. BFB models rely on a `Materials` folder containing `.bfmat` files; both materials and textures may be `shared` between different objects! The default settings should be fine. Refer to the tooltips of the import options for further information.
#### Exporting Models
- `File` > `Export` > `Blue Fang Model (.bfb)`. The default settings should be fine. Sometimes you want to fiddle with / disable the LOD settings, eg. if you created custom / edited the generated LODs.

### Known Limitations
- Animation import of translation keys is sometimes messed up. Animation export is not affected.

### Credits
- Papapanda, Harlequinz Ego & Verdant Gregor for decoding the bulk of the file format
- ZT2 was created by Blue Fang Games for Microsoft Studios.
