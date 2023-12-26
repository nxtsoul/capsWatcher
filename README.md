
# capsWatcher
capsWatcher is a software created in Python using the PyQt framework to indicate the state of toggle keys on the screen using image-based overlays, allowing for easy customization and theme creation by the community. The project was developed based on the need for an open-source, elegant, and customizable tool that allows users to create their own overlay style.

# The capsWatcher service
The capsWatcher service, **`capsWatcher.py`**, was created using the pywin32 API to communicate between Windows modules and functions with Python to obtain the real-time state of keys. It utilizes PyQt to display the overlay on the screen that overlays on top of all windows using Windows' StayOnTop flags. It is important to note that applications using direct communication with the graphics card for rendering, such as games or applications using DirectX or OpenGL, may overlap and ignore the Windows StayOnTop flag.

The overlay is displayed on any screen as capsWatcher showcases the overlay based on the screen where the mouse cursor is located. Therefore, if there are multiple monitors, the overlay will be shown on the monitor where the mouse cursor is present, providing flexibility for users with two or more monitors.


<p align="center"><img src="https://i.imgur.com/oEFmote.gif"></p>

By communicating with data from the configuration file, capsWatcher can monitor more than one toggle key without creating multiple child processes from the primary one. After loading variables and information, it utilizes minimal CPU and RAM, basically weighing as little as a feather on your resources.

Maintaining an icon in the Windows notification area (where the user decides whether it's hidden or not) allows users to access the configuration interface, configure the overlay, terminate, or reload file configurations.

# The capsWatcher configuration interface
The capsWatcher configuration interface, **`capsWatcherInterface.py`**, was developed in conjunction with the capsWatcher service. It enables configuration of the overlay settings such as:
- Overlay display time on the screen in milliseconds (ms)
- Fade-in/out effect time in milliseconds (ms)
- Overlay opacity on the screen
- Overlay position on the screen
- Theme selection
- Color scheme selection (based on the current theme)
- Preview area of how the overlay will appear on the screen with the current settings
- Selection of keys to monitor
- Control to start or stop the capsWatcher service.

It also includes other interface-related settings for the service such as:

- Start with Windows
- Show or hide the icon in the taskbar area
- Interface language selection
- Area to install new themes (which can be created by you)
- Area to check for updates, including an option to never check for updates
- Function to reset all capsWatcher settings to defaults.

<br />
<p align="center">
    <img width="487" src="https://i.imgur.com/xnYpqBo.png">
    <img width="487" src="https://i.imgur.com/OUPH7Ss.png">
</p>

# Themes
The theme section of capsWatcher was conceived with the idea that themes would be created by the community and, if desired, integrated into this repository through pull requests in the `contributed-themes` folder, as long as they follow the recommendations on how to create a theme below. These themes might even appear in an upcoming release of capsWatcher.

## What constitutes a theme?
A theme is structured as a ZIP file containing directories (which we will address shortly), overlay image files, and a JSON file with the theme's name containing standardized information. This allows the capsWatcher configuration interface to import it easily and quickly. How can I create my own?

## The image file
capsWatcher themes can be created using PNG Alpha images that support transparency, recommended to be in dimensions of 128 pixels in height and 128 pixels in width, maintaining a 1:1 aspect ratio. (If it exceeds this size, the preview in the configuration interface will show only the initial 128 pixels for both x and y, which will be addressed in a future version.) However, it can exceed this size as the overlay positions it on the screen by calculating the image dimensions, screen size, and defining the position as selected by the user.

*Note: Currently, capsWatcher only supports monitoring toggle keys like Num Lock, Caps Lock, and Scroll Lock.*

## Naming convention for the image file
In addition to preparing the image, we need to rename it so that capsWatcher can find and define it as the associated key. For this purpose, we use the [key code](https://learn.microsoft.com/en-US/dotnet/api/system.windows.forms.keys?view=windowsdesktop-8.0) and the Boolean state as described below:

**`key code + key state.png`**

Using the analogy described above, let's say we are creating a custom image for the Caps Lock key in the deactivated state. The key code for Caps Lock is **20**, and the Boolean state for the deactivated key is **0**. The textual sum of these items results in a file named **`200.png`**, representing the deactivated state of the Caps Lock key.

## Directory structure of a theme

To ensure smooth operation with capsWatcher themes, we need to follow specific directory structure rules. Inside the `themes` folder of capsWatcher is where themes are stored, each in its own folder with the theme's name. Inside each theme's subfolder, there should be the theme's `*.json`file and subfolders for color schemes, such as `dark` or `light`. These can be defined with other names and updated in the `*.json` file, which we'll cover shortly.

Inside each color scheme folder, the images corresponding to the keys supported in the current theme should be located, following the naming convention mentioned earlier.

Below is an example directory structure starting from the `themes` folder within capsWatcher for the default "Elegant" theme:

```bash
├── themes
│   ├── elegant # Theme folder
│   │   ├── dark # Folder containing images for the dark mode of the theme
│   │   │   ├── 200.png # Image for the Caps Lock key in its deactivated state in dark mode
│   │   │   ├── 201.png # Image for the Caps Lock key in its activated state in dark mode
│   │   │   ├── 1440.png # Image for the Num Lock key in its deactivated state in dark mode
│   │   │   ├── 1441.png # Image for the Num Lock key in its activated state in dark mode
│   │   │   ├── 1450.png # Image for the Scroll Lock key in its deactivated state in dark mode
│   │   │   ├── 1451.png # Image for the Scroll Lock key in its activated state in dark mode
│   │   ├── light # Folder containing images for the light mode of the theme
│   │   │   ├── 200.png # Image for the Caps Lock key in its deactivated state in light mode
│   │   │   ├── 201.png # Image for the Caps Lock key in its activated state in light mode
│   │   │   ├── 1440.png # Image for the Num Lock key in its deactivated state in light mode
│   │   │   ├── 1441.png # Image for the Num Lock key in its activated state in light mode
│   │   │   ├── 1450.png # Image for the Scroll Lock key in its deactivated state in light mode
│   │   │   ├── 1451.png # Image for the Scroll Lock key in its activated state in light mode
│   └── elegant.json # JSON file for theme identification and support in capsWatcher
└────────────────────────
```

This structure represents a complete theme directory for capsWatcher.

## Light and dark modes applied to themes

How can I decide that my theme has a different appearance based on whether the Windows color scheme is light or dark?

To build the color modes of the theme, in addition to having the image in PNG format with the recommended dimensions, we need to decide if this theme will support monitoring the Num Lock only in light mode, Caps Lock only in dark mode, or even Scroll Lock in both color modes.

Knowing this, for each light or dark color scheme, within the theme's folder (as explained in the directory structure above), create a subfolder for each color scheme (it's recommended to name them "dark" for dark mode and "light" for light mode). Each subfolder should contain its overlay images to work in both color schemes if desired. Remember the name of these subfolders, as we will use them to create our theme's JSON file.

After setting up the color scheme folders and their directory structure, create the JSON file so that capsWatcher recognizes the theme. Without it, capsWatcher won't load the theme. Let's move on to the JSON part.

## The theme's JSON file
Each theme must have a JSON file located in the root theme folder (as explained earlier in the theme's directory structure). This file contains information for capsWatcher to identify if it supports multiple color schemes, whether the theme supports monitoring a specific key depending on the color scheme, and general information such as the theme's name and creator details.

The JSON file for a theme is simple with few keys and values. Remember, it must be in the root of the theme folder. Below is an example of a JSON file for the "Elegant" theme in capsWatcher:

```json
{
    "theme": "elegant",
    "name": "Elegant",
    "creator": "Natã Andreghetone",
    "description": "The first and default capsWatcher theme's",
    "github_user": "nxtsoul",
    "creation_date": "2023-11-18 02:39:45",
    "darkMode": {
        "isSupported": true,
        "numLockSupport": true,
        "capsLockSupport": true,
        "scrollLockSupport": true,
        "overlayPath": "dark"
    },
    "lightMode": {
        "isSupported": true,
        "numLockSupport": true,
        "capsLockSupport": true,
        "scrollLockSupport": true,
        "overlayPath": "light"
    }
}
```

Looking at the "Elegant" theme's JSON, we see that key support is divided between color schemes, namely `darkMode` and `lightMode`, with each supporting specific toggle keys.

It's also important to note that if the `isSupported` key of the parent `darkMode` is changed to `false`, capsWatcher will understand that the theme doesn't support dark mode, regardless of whether the key support keys like `numLockSupport` are set to `true`. Therefore, if your theme only supports the Num Lock key, leave the `isSupported` key of the parent `darkMode` as `true`, and the `numLockSupport` key's value as `true`, and so on for other key supports.

Once this step is completed, you can zip the theme and share it via a pull request to be included in future capsWatcher releases.