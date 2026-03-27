const API_BASE_URL = "http://127.0.0.1:8000";

const chartsRoot = document.getElementById("diagram-grid");
const beamViewRoot = document.getElementById("beam-view");
const sourceLabel = document.getElementById("diagram-source");
const summaryLabels = {
  deflection: document.getElementById("max-deflection"),
  moment: document.getElementById("max-moment"),
  shear: document.getElementById("max-shear"),
  nodes: document.getElementById("node-count"),
  elements: document.getElementById("element-count"),
};

document.getElementById("render-diagrams").addEventListener("click", () => {
  loadAndRender();
});

loadAndRender();

async function loadAndRender() {
  const requestPayload = buildRequestPayloadFromInputs();
  try {
    const response = await fetch(`${API_BASE_URL}/analyze/beam`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestPayload),
    });

    if (!response.ok) {
      throw new Error("Beam analysis API request failed.");
    }

    const body = await response.json();
    renderCharts(body);
    sourceLabel.textContent = "Diagramas calculados desde el backend";
  } catch (error) {
    renderCharts(buildFallbackResponse(requestPayload));
    sourceLabel.textContent = "Mostrando caso de ejemplo local";
  }
}

function renderCharts(data) {
  chartsRoot.innerHTML = "";
  beamViewRoot.innerHTML = "";
  summaryLabels.deflection.textContent = `${formatNumber(data.summary.max_deflection_mm)} mm`;
  summaryLabels.moment.textContent = `${formatNumber(data.summary.max_moment_kNm)} kNm`;
  summaryLabels.shear.textContent = `${formatNumber(data.summary.max_shear_kN)} kN`;
  summaryLabels.nodes.textContent = formatNumber(data.summary.total_nodes);
  summaryLabels.elements.textContent = formatNumber(data.summary.total_elements);

  const orderedTypes = ["shear", "moment", "deflection"];
  orderedTypes.forEach((type) => {
    const diagram = data.diagrams.find((item) => item.diagram_type === type);
    if (!diagram) {
      return;
    }
    chartsRoot.appendChild(buildChartCard(diagram));
  });

  if (data.nodes) {
    beamViewRoot.appendChild(createBeamView(data));
  }
}

function buildChartCard(diagram) {
  const card = document.createElement("article");
  card.className = "diagram-card";

  const header = document.createElement("div");
  header.className = "diagram-card-header";
  header.innerHTML = `<h3>${translateDiagramType(diagram.diagram_type)}</h3><span>${diagram.unit}</span>`;

  const svg = createLineChart(diagram.points, diagram.diagram_type);
  const footer = document.createElement("div");
  footer.className = "diagram-card-footer";
  footer.textContent = describeDiagram(diagram);

  card.append(header, svg, footer);
  return card;
}

function createLineChart(points, type) {
  const width = 520;
  const height = 220;
  const padding = 26;
  const normalizedPoints = (() => {
    if (type !== "shear" || points.length < 2) {
      return points;
    }

    const nextPoints = [...points];
    const firstPoint = nextPoints[0];
    const secondPoint = nextPoints[1];
    if (firstPoint.x_m === secondPoint.x_m && Math.abs(firstPoint.value) > 1e-9) {
      nextPoints.unshift({ x_m: firstPoint.x_m, value: 0 });
    }

    const lastPoint = nextPoints[nextPoints.length - 1];
    const previousPoint = nextPoints[nextPoints.length - 2];
    if (lastPoint.x_m === previousPoint.x_m && Math.abs(lastPoint.value) > 1e-9) {
      nextPoints.push({ x_m: lastPoint.x_m, value: 0 });
    }

    return nextPoints;
  })();

  const xValues = normalizedPoints.map((point) => point.x_m);
  const yValues = normalizedPoints.map((point) => point.value);
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  const minY = Math.min(...yValues, 0);
  const maxY = Math.max(...yValues, 0);
  const ySpan = maxY - minY || 1;
  const xSpan = maxX - minX || 1;
  const zeroY = padding + ((maxY - 0) / ySpan) * (height - padding * 2);
  const getChartX = (value) => padding + ((value - minX) / xSpan) * (width - padding * 2);
  const getChartY = (value) => padding + ((maxY - value) / ySpan) * (height - padding * 2);
  const axisStartX = normalizedPoints.length ? getChartX(normalizedPoints[0].x_m) : padding;
  const axisEndX = normalizedPoints.length ? getChartX(normalizedPoints[normalizedPoints.length - 1].x_m) : width - padding;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("class", `diagram-svg ${type}`);

  const axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
  axis.setAttribute("x1", String(axisStartX));
  axis.setAttribute("x2", String(axisEndX));
  axis.setAttribute("y1", String(zeroY));
  axis.setAttribute("y2", String(zeroY));
  axis.setAttribute("class", "axis-line");
  svg.appendChild(axis);
  const pathData = normalizedPoints
    .map((point, index) => {
      const x = getChartX(point.x_m);
      const y = getChartY(point.value);
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", pathData);
  path.setAttribute("class", "diagram-line");
  svg.appendChild(path);

  normalizedPoints.forEach((point) => {
    const x = getChartX(point.x_m);
    const y = getChartY(point.value);

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", String(x));
    circle.setAttribute("cy", String(y));
    circle.setAttribute("r", "4");
    circle.setAttribute("class", "diagram-point");
    svg.appendChild(circle);
  });

  return svg;
}

function describeDiagram(diagram) {
  const maxAbs = Math.max(...diagram.points.map((point) => Math.abs(point.value)));
  return `Valor máximo: ${formatNumber(maxAbs)} ${diagram.unit}`;
}

function translateDiagramType(type) {
  return {
    shear: "Diagrama de cortante",
    moment: "Diagrama de momentos",
    deflection: "Deformada",
  }[type] || type;
}

function formatNumber(value) {
  return new Intl.NumberFormat("es-ES", { maximumFractionDigits: 3 }).format(value);
}

function buildRequestPayloadFromInputs() {
  const length = Number(document.getElementById("beam-length").value);
  const elementCount = Number(document.getElementById("beam-elements").value);
  const load = Number(document.getElementById("beam-load").value);
  const modulus = Number(document.getElementById("beam-e").value);

  return {
    project_name: "Beam example",
    span: {
      length_m: length,
      element_count: elementCount,
    },
    material: {
      modulus_of_elasticity_mpa: modulus,
    },
    section: {
      width_mm: 63.0,
      depth_mm: 200.0,
    },
    supports: [
      { position_m: 0.0, support_type: "pinned" },
      { position_m: length, support_type: "roller" },
    ],
    loads: [
      {
        load_type: "distributed",
        start_m: 0.0,
        end_m: length,
        value_kN_per_m: load,
      },
    ],
  };
}

function buildFallbackResponse(payload) {
  const length = payload.span.length_m;
  const elements = payload.span.element_count;
  const q = payload.loads[0].value_kN_per_m;
  const e = payload.material.modulus_of_elasticity_mpa;
  const inertia = (63 * Math.pow(200, 3)) / 12;
  const loadMagnitude = Math.abs(q);
  const maxMoment = (loadMagnitude * Math.pow(length, 2)) / 8;
  const maxShear = (loadMagnitude * length) / 2;
  const maxDeflection = (5 * loadMagnitude * Math.pow(length * 1000, 4)) / (384 * e * inertia);
  const nodeCount = elements + 1;
  const step = length / elements;

  const nodes = [];
  const shearPoints = [];
  const momentPoints = [];
  const deflectionPoints = [];
  const appendPoint = (points, x, value) => {
    const lastPoint = points[points.length - 1];
    if (lastPoint && lastPoint.x_m === x && Math.abs(lastPoint.value - value) < 1e-9) {
      return;
    }
    points.push({ x_m: x, value });
  };

  for (let index = 0; index < nodeCount; index += 1) {
    const x = index * step;
    const shear = maxShear - loadMagnitude * x;
    const moment = (loadMagnitude * x * (length - x)) / 2;
    const deflection =
      -(
        (loadMagnitude * 1000 * x * 1000) /
        (24 * e * inertia)
      ) *
      (Math.pow(length * 1000, 3) - 2 * length * 1000 * Math.pow(x * 1000, 2) + Math.pow(x * 1000, 3));

    nodes.push({
      node_id: index,
      x_m: x,
      vertical_displacement_mm: deflection,
      rotation_rad: 0,
    });
    if (index === 0) {
      appendPoint(shearPoints, x, 0);
      appendPoint(shearPoints, x, maxShear);
      appendPoint(momentPoints, x, 0);
    } else if (index === nodeCount - 1) {
      appendPoint(shearPoints, x, shear);
      appendPoint(shearPoints, x, 0);
      appendPoint(momentPoints, x, 0);
    } else {
      appendPoint(shearPoints, x, shear);
      appendPoint(momentPoints, x, moment);
    }
    deflectionPoints.push({ x_m: x, value: deflection });
  }

  return {
    summary: {
      total_nodes: nodeCount,
      total_elements: elements,
      max_deflection_mm: maxDeflection,
      max_deflection_position_m: length / 2,
      max_moment_kNm: maxMoment,
      max_shear_kN: maxShear,
    },
    nodes,
    diagrams: [
      {
        diagram_type: "shear",
        unit: "kN",
        points: shearPoints,
      },
      {
        diagram_type: "moment",
        unit: "kNm",
        points: momentPoints,
      },
      {
        diagram_type: "deflection",
        unit: "mm",
        points: deflectionPoints,
      },
    ],
  };
}

function createBeamView(data) {
  const width = 900;
  const height = 260;
  const padding = 40;
  const nodes = data.nodes;
  const xMin = nodes[0].x_m;
  const xMax = nodes[nodes.length - 1].x_m;
  const xSpan = xMax - xMin || 1;
  const baseY = height / 2;
  const maxAbsDeflection = Math.max(...nodes.map((node) => Math.abs(node.vertical_displacement_mm))) || 1;
  const scaleY = 70 / maxAbsDeflection;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("class", "beam-svg");

  const baseline = document.createElementNS("http://www.w3.org/2000/svg", "line");
  baseline.setAttribute("x1", String(padding));
  baseline.setAttribute("x2", String(width - padding));
  baseline.setAttribute("y1", String(baseY));
  baseline.setAttribute("y2", String(baseY));
  baseline.setAttribute("class", "beam-baseline");
  svg.appendChild(baseline);

  const deformed = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  deformed.setAttribute(
    "points",
    nodes
      .map((node) => {
        const x = padding + ((node.x_m - xMin) / xSpan) * (width - padding * 2);
        const y = baseY + node.vertical_displacement_mm * scaleY;
        return `${x},${y}`;
      })
      .join(" "),
  );
  deformed.setAttribute("class", "beam-deformed");
  svg.appendChild(deformed);

  nodes.forEach((node, index) => {
    const x = padding + ((node.x_m - xMin) / xSpan) * (width - padding * 2);
    const y = baseY + node.vertical_displacement_mm * scaleY;

    const point = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    point.setAttribute("cx", String(x));
    point.setAttribute("cy", String(y));
    point.setAttribute("r", index === 0 || index === nodes.length - 1 ? "4.5" : "2.5");
    point.setAttribute("class", "beam-node");
    svg.appendChild(point);
  });

  appendSupport(svg, padding, baseY, "pinned");
  appendSupport(svg, width - padding, baseY, "roller");
  return svg;
}

function appendSupport(svg, x, baseY, type) {
  const triangle = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
  triangle.setAttribute(
    "points",
    `${x - 16},${baseY + 30} ${x + 16},${baseY + 30} ${x},${baseY + 6}`,
  );
  triangle.setAttribute("class", "beam-support");
  svg.appendChild(triangle);

  if (type === "roller") {
    [-8, 8].forEach((offset) => {
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", String(x + offset));
      circle.setAttribute("cy", String(baseY + 38));
      circle.setAttribute("r", "4");
      circle.setAttribute("class", "beam-support");
      svg.appendChild(circle);
    });
  }
}
