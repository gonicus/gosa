qx.Class.define("cute.ui.table.Table",
{
  extend : qx.ui.table.Table,

  construct: function(tableModel, customModel)
  {
    // Create column model
    if(!customModel){
      customModel = {
        tableColumnModel : function(obj){
          return new qx.ui.table.columnmodel.Resize(obj);
        }
      }
    }

    this.base(arguments, tableModel, customModel);

    // Add additional key 
    this.addListener('keyup', function(e){

      // Select all table entries when Strg+A is pressed.
      if(e.getKeyIdentifier() == 'A' && e.isCtrlPressed()){
        this.getSelectionModel().setSelectionInterval(0, this.getTableModel().getRowCount()-1);
      }

      // Send 'remove' event if 'del' is pressed.
      if(e.getKeyIdentifier() == 'Delete'){
        this.fireEvent('remove');
      }

    },this);

    // Fire an edit event when clicking twice on the table.
    this.addListener('dblclick', function(){
        this.fireEvent('edit');
    }, this);

    // Store table preferences back on disappear.
    this.addListener('disappear', function(){
        this.saveUserPreferences();
    }, this);

    // Sort for column descending as default.
    this.__defaultPreferences = {0: 3};
    this.__lastPreferences = {};
  },

  events :
  {
      "edit" : "qx.event.type.Event",
      "remove" : "qx.event.type.Event"
  },

  
  destruct : function()
  {
      this.__lastPreferences = this.__defaultPreferences = this.__recurrentSeconds = null;
      this.__timer = null;
  },


  members :
  {
    __preferenceName: null,
    __lastPreferences: null,
    __defaultPreferences: null,


    /*! \brief  Collects table preferences like sorting direction
     *           and visible columns and save these information back to
     *           current user model.
     */
    saveUserPreferences: function()
    {
      // We do not have a table preference name defined, just return.
      if(this.__preferenceName == null){
        new qx.core.Object().debug('No table prefrence name defined, cannot store table preferences!');
        return;
      }


      var cModel = this.getTableColumnModel();
      var columnCount = cModel.getOverallColumnCount();
      var prefs = {}; 

      // Walk through columns and collect their states.
      for(var i=0; i<columnCount; i++){
        var id = 0;

        // Get column visibility state.
        if(this.getTableColumnModel().isColumnVisible(i)){
          id |= 1;
        }

        // Get colum sort state.
        if(this.getTableModel().getSortColumnIndex() == i){
          if(this.getTableModel().isSortAscending()){
            id |= 2;
          }else{
            id |= 4;
          }
        }
        prefs[i] = id;
      }

      // Save settings back to the user model
      if(cute.Session.getUser() && !this.comparePreferences(prefs, this.__lastPreferences)){
        //#TODO: Save user preoferences somewhere
        //cute.Session.getUser().setTablePreferences(this.__preferenceName, prefs);

      }
      this.__lastPreferences = prefs;
    },


    /*! \brief  Compare two preference objects. Returns true if they match.
    */ 
    comparePreferences:  function(x,y)
    {
      for(var p in x){
        if(y[p] === null ||  x[p] != y[p]){
          return(false);
        }
      }
      for(var p in y){
        if(x[p] === null ||  y[p] != x[p]){
          return(false);
        }
      }
      return(true);
    },

    sort: function(){
      this.getTableModel().sortByColumn(this.getTableModel().getSortColumnIndex(), this.getTableModel().isSortAscending()); 
    },


    /* \brief   Load table preferences like sorting, visible columns etc. 
     *           from the current user model.
     */
    loadUserPreferences: function()
    {
      // We do not have a table preference name defined, just return.
      if(this.__preferenceName == null || cute.Session.getUser() == null){
        return;
      }

      // Check the user model for table preferences 
      //TODO: load user preferences somewhere
      var prefs = null;

      // If no preferences were defined, then use the default preferences.
      if(prefs == null){
        prefs = this.__defaultPreferences;
      }

      var cModel = this.getTableColumnModel();
      var columnCount = cModel.getOverallColumnCount();

      // Walk through active columns and set their state.
      for(var i=0; i<columnCount; i++){
        if(prefs[i] != null) {

          // Hide or show column
          var active = prefs[i] != 0;
          this.getTableColumnModel().setColumnVisible(i,active);

          // Set sort column ascending
          if(prefs[i] & 2){
            this.getTableModel().sortByColumn(i, true);
          }

          // Set sort column descending
          if(prefs[i] & 4){
            this.getTableModel().sortByColumn(i, false);
          }
        }else{
          // Column not defined in prefs.
        }
      }

      // Remember the current settigs, so we can decide when a save is needed.
      this.__lastPreferences = prefs;
    },


    /*! \brief  Set a table-preference name, which allows us to store
     *           table preferences like, sorting, visible colums etc. 
     *           in the loggedin-user model.
     */
    setPreferenceTableName: function(name, defaultPrefs)
    {
      if(defaultPrefs != null){
        this.__defaultPreferences = defaultPrefs;
      }

      this.__preferenceName = name;
      this.loadUserPreferences();
    }
  }
});
// vim:tabstop=2:expandtab:shiftwidth=2
