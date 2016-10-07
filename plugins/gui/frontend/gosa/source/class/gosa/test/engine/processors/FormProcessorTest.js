qx.Class.define("gosa.test.engine.processors.FormProcessorTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    __processor : null

    // NOTE: As the form processor is currently not used, this test is ignored.

    // setUp : function() {
    //   this.__processor = new gosa.engine.processors.FormProcessor();
    // },

    // tearDown : function() {
    //   this.__processor.dispose();
    //   this.__processor = null;
    // },

    // testFormCreation : function() {
    //   var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
    //   var symTable = gosa.engine.SymbolTable.getInstance();

    //   var json = {
    //     type : "form",
    //     symbol : "testForm",
    //     label : "Foo",
    //     renderer : "qx.ui.form.renderer.Single",
    //     elements : [
    //       {
    //         group : "Standard text field"
    //       },
    //       {
    //         "class" : "qx.ui.form.TextField",
    //         label : "A text field",
    //         modelPath : "test.textField",
    //         properties : {
    //           value : "Test Text Field"
    //         },
    //         symbol : "testTextField"
    //       },
    //       {
    //         group : "Visibility toggled by check box"
    //       },
    //       {
    //         "class" : "qx.ui.form.CheckBox",
    //         label : "Obviously, a check box",
    //         symbol : "checkBox"
    //       },
    //       {
    //         "class" : "qx.ui.form.TextField",
    //         label : "Visible, when check box is checked",
    //         symbol : "visibleTextField",
    //         visibilityDependsOn : "@checkBox"
    //       },
    //       {
    //         "class" : "qx.ui.form.TextField",
    //         label : "Visible, when check box is unchecked",
    //         symbol : "invisibleTextField",
    //         visibilityDependsOn : "!@checkBox"
    //       }
    //     ]
    //   };
    //   this.__processor.process(json, container);

    //   this.assertInstance(symTable.resolveSymbol("testForm"), qx.ui.form.Form);

    //   this.assertEquals(1, container.getChildren().length);

    //   var groupBox = container.getChildren()[0];
    //   this.assertEquals("Foo", groupBox.getLegend());
    //   this.assertInstance(groupBox, qx.ui.groupbox.GroupBox);
    //   this.assertEquals(2, groupBox.getChildren().length);
    //   this.assertEquals(groupBox, symTable.resolveSymbol("testFormWidget"));

    //   var errorBox = groupBox.getChildren()[1];
    //   this.assertInstance(errorBox, qx.ui.container.Composite);

    //   var renderer = groupBox.getChildren()[0];
    //   this.assertInstance(renderer, qx.ui.form.renderer.Single);

    //   var textField = symTable.resolveSymbol("testTextField");
    //   this.assertInstance(textField, qx.ui.form.TextField);
    //   this.assertEquals("test.textField", textField.getUserData("modelPath"));
    //   this.assertEquals("Test Text Field", textField.getValue());

    //   // check box and visibility toggling
    //   var checkBox = symTable.resolveSymbol("checkBox");
    //   this.assertInstance(checkBox, qx.ui.form.CheckBox);

    //   var visibleTextField = symTable.resolveSymbol("visibleTextField");
    //   this.assertInstance(visibleTextField, qx.ui.form.TextField);
    //   this.assertFalse(visibleTextField.isVisible());

    //   var invisibleTextField = symTable.resolveSymbol("invisibleTextField");
    //   this.assertInstance(invisibleTextField, qx.ui.form.TextField);
    //   this.assertTrue(invisibleTextField.isVisible());

    //   // toggle check box
    //   checkBox.setValue(true);
    //   this.assertTrue(visibleTextField.isVisible());
    //   this.assertFalse (invisibleTextField.isVisible());

    //   container.dispose();
    // }
  }
});
