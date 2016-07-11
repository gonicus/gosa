qx.Class.define("gosa.ui.container.MergeItem", {
	extend: qx.ui.form.ToggleButton,
	construct: function(widget){
		this.base(arguments);
		this._setLayout(new qx.ui.layout.HBox());
		this._add(widget, {flex: 1});
        this.setDecorator("white-box");
	}
});
