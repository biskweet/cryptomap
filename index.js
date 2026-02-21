const cytoscape = require("cytoscape");
const cola = require('cytoscape-cola');

const fs = require("fs");


cytoscape.use(cola);

const OUTFILE = "public/data.json"


const exportGraph = (cy) => {
    const elements = [
        ...cy.nodes().map(n => ({
            group: 'nodes',
            data: n.data(),
            position: n.position()
        })),
        ...cy.edges().map(e => ({
            group: 'edges',
            data: e.data()
        }))
    ];
    return JSON.stringify(elements);
};


const reorderData = (data) => {
    const nodes = data.nodes;
    const edges = data.edges;

    nodes.sort((n1, n2) => parseInt(n1.data.year || "1970") - parseInt(n2.data.year || "1970"));
    const nodeIds = nodes.map(node => node.data.id);

    edges.sort((e1, e2) =>
        nodeIds.indexOf(e1.data.source) * 1e6 + nodeIds.indexOf(e1.data.target)
            - nodeIds.indexOf(e2.data.source) * 1e6 + nodeIds.indexOf(e2.data.target)
    );

    return nodes.concat(edges);
}


const fileData = fs.readFileSync("data-clean.json", { encoding: 'utf-8' });
const data = reorderData(JSON.parse(fileData));

const style_data = [
    {
        selector: 'node',
        style: {
            'shape': 'round-rectangle',
            'width': 'label',
            'height': 'label',
            'padding': '10px',

            'background-color': '#fff',
            'border-width': 2,
            'border-color': '#0074D9',
            'border-opacity': 0.8,

            'label': function(node) {
                return node.data('label') + '\n' + node.data('year');
            },

            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#333',
            'font-family': 'Helvetica, Arial, sans-serif',
            'font-size': '12px',

            'text-wrap': 'wrap',
            'text-max-width': '100px',

            'ghost': 'no',
            'text-events': 'no',
        }
    },
    {
        selector: '.highlighted',
        style: {
            'background-color': '#FF851B',
            'transition-property': 'background-color, line-color',
            'transition-duration': '0.3s'
        },
    },
    {
        selector: 'edge',
        style: {
            'width': 2,
            'line-color': '#999',
            'target-arrow-color': '#999',
            'target-arrow-shape': 'triangle',
            'curve-style': 'straight',
            'control-point-step-size': 40
        }
    }
]

const layout_cose = {
    name: 'cose',
    randomize: false,
    refresh: 100_000_000,
    fit: false,
    infinite: false,
    padding: 30,
    gravity: 0.2,
    nodeRepulsion: 500000,

    edgeLength: function(edge) {
        return 15000 + edge.source().degree() * 5000;
    },

    nodeSpacing: function(node) {
        return 15000 + node.degree() * 5000;
    }
}

const layout_cola = {
    name: 'cola',
    randomize: false,
    animate: true,
    refresh: 100_000_000,
    fit: true,
    infinite: false,
    padding: 30,
    gravity: 0.9,
}

console.log("Building graph with", data.length, "elements...");

const cy = cytoscape({
    container: null,
    headless: true,
    elements: data,
});

cy.layout(layout_cose).run();

console.log("Layout 1 done.");

//cy.layout(layout_cola).run();

console.log("Exporting...");

const result = exportGraph(cy);

console.log("Writing", result.length, "bytes");

fs.writeFileSync(OUTFILE, result);

