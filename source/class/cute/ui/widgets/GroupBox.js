/* This group-box widget is derived from the qooxdoos original group-box, 
 * it has the ability to hide itself, if all child elements are hidden.
 * */
qx.Class.define("cute.ui.widgets.GroupBox", {

  extend: qx.ui.groupbox.GroupBox,

  construct: function(title){
    this.base(arguments, title);

    // Collect all cute child widgets on appear
    // This required to be able to hide the complete group box 
    // when no visible item is left (for details see BlockedBy).
    this.__cuteChildList = [];
    this.addListenerOnce("appear", function(){
        this.__cuteChildList = this.loadChildrenList(this.getChildren());

        // Now check if we have to hide ourselfes due to the fact that
        // no visible item is left or not.
        this.__check();
      }, this);
  },

  destruct : function(){
    this._disposeArray("__cuteChildList");
  },

  members: {

    __cuteChildList: null,
    
    /* Check if all elements of this group-box are hidden, in this case
     * hide the group box too.
     * */
    __check: function(){
      var disable = true;
      for(var i=0; i<this.__cuteChildList.length; i++){
        if(this.__cuteChildList[i].getVisibility() == "visible"){
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
     * Add a listener to all found cute-widgets to receive events about their
     * visiblity status.
     * Returns all found cuteWidgets
     * */
    loadChildrenList: function(current){
      var children = [];
      for(var i=0; i< current.length; i++){

        if(current[i].hasState && current[i].hasState("cuteInput")){
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
