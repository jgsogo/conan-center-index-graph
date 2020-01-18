import _ from 'lodash';
import './style.css';
import data from './data.json';
import style from './cy-style.json';

import {cytoscape, toJSON, printMe} from './graph.js';
//import {toJson, cytoscape} from './graph.js';


function component() {
    const element = document.createElement('div');
    const btn = document.createElement('button');

    element.innerHTML = _.join(['Hello', 'webpack'], ' ');
    element.classList.add('hello');

    btn.innerHTML = 'Click me and check the console!';
    btn.onclick = printMe;

    element.appendChild(btn);

    console.log(style);

    return element;
}

/*
function create_graph() {
    const element = document.createElement('div');
    const style = 23; //fetch('cy-style.json').then(toJson);
    const data = 42; //fetch('data.json').then(toJson);
    return cytoscape(element, data, style);
}
*/

document.body.appendChild(component());
//document.body.appendChild(create_graph());