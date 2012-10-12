/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.dialogs.Dialog",
{
  extend : qx.ui.window.Window,

  construct : function(caption, icon)
  {
    this.base(arguments, caption, icon);

    // Minimum sizes
    this.setMinWidth(300);
    this.setMinHeight(120);
    this.addListener("appear", this.__onAppear, this);

    // Basic setup
    this.setModal(true);
    this.setShowClose(false);
    this.setShowMaximize(false);
    this.setShowMinimize(false);
    this.setAlwaysOnTop(true);
    this.setResizable(false, false, false, false);

    // Set layout and prepare the dialog view
    this.setLayout(new qx.ui.layout.VBox(5));

    // Build button pane
    var paneLayout = new qx.ui.layout.HBox().set({
      spacing: 4,
      alignX : "right"
    });
    this._buttonPane = new qx.ui.container.Composite(paneLayout).set({
      paddingTop: 11
    });
    this.add(this._buttonPane);
  },


  properties :
  {
    focusOrder :
    {
      check : "Array",
      apply : "__applyFocusOrder",
      init  : []
    }
  },


  members : {

    addButton : function(button)
    {
        this._buttonPane.add(button);
    },

    addElement : function(element, options)
    {
        this.addBefore(element, this._buttonPane, options);
    },

    /**
     * Called whenever a window appears on the screen.
     * Sets the focus on first input field and registers the window 
     *  in the list of currenlty opened windows.
     * (Since a window is opened the GE plugin cannot appear.)
     *
     * @return {void} 
     */
    __onAppear : function()
    {
      this.center(); 
      this.setEnabled(true);
      this.setActive(true);

      try{
        if (this.getFocusOrder().length){
          var item = this.getFocusOrder()[0];
          if(item == null || !item.isFocusable()){
            this.debug("Could not set focus for " + item);
          }else{
            item.setEnabled(true);
            item.focus();
          }
        }
      }catch(e){
        this.debug("Failed to handle focus order, please check property 'focusOrder' for " + this + " --> " +e );
        this.debug(this.getFocusOrder());
      }
    },


    /**
     * Sets the order of the focus. 
     *
     * @param args {Array} An array, containing the widgets to set focus on.
     * @return {void} 
     */
    __applyFocusOrder : function(args)
    {
      // Set focus on next field
      try
      {
        for (var i=0; i<args.length; i++){
          args[i].addListener("keyup", this.checkInput, this);
        }
      }
      catch(e)
      {
        this.debug("Failed to handle focus order!");
        this.debug(args);
      }
    },


    /**
     * On each ENTER keypress we have to switch to the next input widget.
     *
     * @param e {Event} Key press event 
     * @return {void} 
     */
    checkInput : function(e)
    {
      // Set focus to next button
      if (e.getKeyIdentifier() == "Enter")
      {
        // Set focus on nect field, if next is a button then execute it
        var set = false;

        for (var i=0; i<this.getFocusOrder().length; i++)
        {
          var item = this.getFocusOrder()[i];

          if (set)
          {
            if (item instanceof qx.ui.form.Button)
            {
              item.focus();
              setTimeout(function() {
                item.focus();
              });

              item.execute();
            }
            else
            {
              setTimeout(function() {
                item.focus();
              });
              item.focus();
            }

            return;
          }

          // Found field that has currently the focus
          if (item.hasState("focused")) {

            if (item instanceof qx.ui.form.TextArea)
            {
              // Don't send the Enter key event somewhere
              e.stopPropagation();
              return;
            }

            if (item instanceof qx.ui.form.Button)
            {
              setTimeout(function() {
                item.focus();
              });
              item.focus();
              item.execute();
              return;
            }

            set = true;

          }
        }
      }
    }
  }
});
