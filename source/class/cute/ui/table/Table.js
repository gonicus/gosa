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
                cute.Session.getUser().setTablePreferences(this.__preferenceName, prefs);
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
                        this.sortBy(i, true);
                    }

                    // Set sort column descending
                    if(prefs[i] & 4){
                        this.sortBy(i, false);
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
        },


        /*! \brief   Reset the table model selection.
         */
        resetSelection: function()
        {
            this.getSelectionModel().resetSelection();
        },

        /*! \brief  Sorts the table model by the given column-ID and 
         *           sort direction.
         * @param   Integer     The column-ID to sort for.
         * @param   Boolean     The sort direction, true=acending.
         */
        sortBy: function(col, asc)
        {
            if(this.getTableModel().setSortColumnIndexWithoutSortingData){
                this.getTableModel().setSortColumnIndexWithoutSortingData(col);
                this.getTableModel().setSortAscendingWithoutSortingData(asc);
            }else{
                this.getTableModel().sortByColumn(col, asc);
            }
        },

       
        /* \brief   Disabled sorting for the given column-Ids 
         * @param   Array   The column-IDs to disable sorting for.
         */ 
        disableSorting: function(array)
        {
            for(var i=0; i< array.length; i++){
                this.getTableModel().setColumnSortable(array[i], false);
            }
        },

        
        /*! \brief      Returns a list of all selected item-models of cached entries.
         */
        getSelectedItems: function()
        {
            var items = [];
            this.getSelectionModel().iterateSelection(function(ind) {
                    var o = this.getTableModel().getRowData(ind);
                    if(o){
                        items.push(o);
                    }
                },this);     
            return(items);
        },


        /*! \brief      Returns a list of all selected item-ids of cached entries.
         */
        getSelectedIds: function()
        {
            var items = [];
            this.getSelectionModel().iterateSelection(function(ind) {
                    items.push(ind);
                },this);     
            return(items);
        },



        /*! \brief      Returns the numer of entries selected in the table.
         */
        getSelectedItemCount: function()
        {
            var cnt = 0;
            this.getSelectionModel().iterateSelection(function(ind) {
                    if(this.getTableModel().getRowData(ind)){
                        cnt ++;
                    }
                }, this);     
            return(cnt);
        },


        /*! \brief      Returns ALL selected items in the table also uncached entries.
         */
        getSelectedItemsComplete: function(func, context)
        {
            if(this.getSelectionModel().getSelectedCount() != this.getSelectedItemCount()){
                var ranges = this.getSelectionModel().getSelectedRanges();
                for(var i=0; i<ranges.length; i++){
                    var listener = null;
                    var model = this.getTableModel();
                    listener = model.addListener('dataChanged', function(){
                            model.removeListenerById(listener);
                            func.call(context, this.getSelectedItems());
                        }, this);
                    model.prefetchRows(ranges[i].minIndex, ranges[i].maxIndex);
                }
            }else{
                func.call(context, this.getSelectedItems());
            }
        }
    }
});
