import pkg_resources

class GuiPlugin:

    def __init__(self):
        print("Heureka!")
        print(pkg_resources.resource_filename('gosa.plugin.gui', 'frontend/build'))
