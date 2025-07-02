# autodig
<p align "center">
   Auto-Dig script for <a href="https://www.roblox.com/games/126244816328678/DIG">DIG</a>
</p>


## Install
1. **Clone repo**
    ```sh
    git clone https://github.com/jules-party/autodig
    cd autodig
    ```
2. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    ```

3. **Config setup**
    ```sh
    mv exconfig.yml config.yml
    ```

## Running
> [!NOTE]
> I am working on a GUI written using Tkinter for easy use, but for right now you can only run it using the console program

```sh
python dig.py
```

## Configuration
* **debug**
    - Enable debug window
* **skip_rectangle**
    - Use rectangle data saved to config
* **rectangle**
    - Rectangle data for where the bar is located on your screen
