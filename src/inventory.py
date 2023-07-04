# This module contains all classes and functions which involve
# inventory items.

class InventoryState():

    # This class contains the state of the player's inventory,
    # along with methods to extract desired information.

    def __init__(self, inventory_list):

        # 'inventory_list' is the data structure returned by the 
        # auto-player driver's `get_inventory_list` method.

        self.inventory = inventory_list 

    def get_item_type(self, item_type):

        # This method returns all items which match the passed
        # 'item_type' string.

        items = [
            i_dict for i_dict in self.inventory if item_type in i_dict["type"]
        ]
        return items
    
    def get_item(self, name):

        # This method returns all items which match the
        # passed item name exactly.

        items = [
            i_dict for i_dict in self.inventory if name == i_dict["name"]
        ]
        return items
    
    def get_all(self):
        
        # This function returns every inventory item.

        return self.inventory
