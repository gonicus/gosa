/* This group-box widget is derived from the qooxdoos original group-box, 
 * it has the ability to hide itself, if all child elements are hidden.
 * */
qx.Class.define("gosa.ui.widgets.GroupBox", {

  extend: qx.ui.groupbox.GroupBox,

  construct: function(title){
    this.base(arguments, title);

    // Collect all gosa child widgets on appear
    // This required to be able to hide the complete group box 
    // when no visible item is left (for details see BlockedBy).
    this.__gosaChildList = [];
    this.addListenerOnce("appear", function(){
        this.__gosaChildList = this.loadChildrenList(this.getChildren());

        // Now check if we have to hide ourselfes due to the fact that
        // no visible item is left or not.
        this.__check();
      }, this);
  },

  destruct : function(){

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this); 

    this._disposeArray("__gosaChildList");
  },

  members: {

    __gosaChildList: null,
    
    /* Check if all elements of this group-box are hidden, in this case
     * hide the group box too.
     * */
    __check: function(){
      var disable = true;
      for(var i=0; i<this.__gosaChildList.length; i++){
        if(this.__gosaChildList[i].getVisibility() == "visible"){
          disable = false;
          break;
        }
      }
      if(disable){
        this.exclude();
      }else{
        this.show();
      }
    },

    /* Recursivly load all child elements of the given qooxdoo widget.
     * Add a listener to all found gosa-widgets to receive events about their
     * visiblity status.
     * Returns all found gosaWidgets
     * */
    loadChildrenList: function(current){
      var children = [];
      for(var i=0; i< current.length; i++){

        if(current[i].hasState && current[i].hasState("gosaInput")){
          children.push(current[i]); 
          current[i].addListener("changeVisibility", this.__check, this);      
        }

        if(current[i].getChildren){
          children = children.concat(this.loadChildrenList(current[i].getChildren()));
        }
      }
      return(children);
    }
  }
});
