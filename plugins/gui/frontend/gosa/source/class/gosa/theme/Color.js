/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Theme.define("gosa.theme.Color",
{
  extend : qx.theme.indigo.Color,

  colors :
  {
    'header-bar' : 'black',
    'header-text' : 'white',
    'error-text': '#8A0808',
    'disabled-text': '#CCCCCC',
    'hovered': '#DDD',
    'icon-color': '#666666',
    'border-separator' : 'mediumgray-light',
    "highlight" : "#3D72C9", // bright blue

    "background-selected" : "aqua-dark",
    "table-focus-indicator" : "transparent",
    "table-row-background-selected" : "aqua-dark",
    "table-row-background-focused-selected" : "aqua-dark",

    // - FLAT - do not insert anything behind this marker -----------------------------------------------------
    'white' : '#FFF',
    'black' : '#000',

    'bluejeans-dark' : '#4A89DC',
    'bluejeans-light' : '#5D9CEC',

    'aqua-dark' : '#3BAFDA',
    'aqua-light' : '#4FC1E9',

    'mint-dark' : '#37BC9B',
    'mint-light' : '#48CFAD',

    'grass-dark' : '#8CC152',
    'grass-light' :'#A0D468',

    'sunflower-dark' : '#F6BB42',
    'sunflower-light' : '#FFCE54',

    'bittersweet-dark' : '#E9573F',
    'bittersweet-light' : '#FC6E51',

    'grapefruit-dark' : '#DA4453',
    'grapefruit-light' : '#ED5565',

    'lavender-dark' : '#967ADC',
    'lavender-light' : '#AC92EC',

    'pinkrose-dark' : '#D770AD',
    'pinkrose-light' : '#EC87C0',

    'lightgray-dark' : '#E6E9ED',
    'lightgray-light' : '#F5F7FA',

    'mediumgray-dark' : '#AAB2BD',
    'mediumgray-light' : '#CCD1D9',

    'darkgray-dark' : '#434A54',
    'darkgray-light' : '#656D78'
  }
});
