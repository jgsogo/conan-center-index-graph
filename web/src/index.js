import _ from 'lodash';
import './style.css';
import data from './data.json';
import style from './cy-style.json';

import {get_graph, toJSON, printMe} from './graph.js';
//import {toJson, cytoscape} from './graph.js';

function component() {
    const element = document.createElement('h1');
    const btn = document.createElement('button');

    element.innerHTML = _.join(['Hello', 'webpack'], ' ');
    element.classList.add('hello');

    btn.innerHTML = 'Click me and check the console!';
    btn.onclick = printMe;

    element.appendChild(btn);
    return element;
}


function create_graph() {
    const element = document.createElement('div');

    console.log(style);
     get_graph(element, data, style);
     return element;
}


document.body.appendChild(component());
document.body.appendChild(create_graph());