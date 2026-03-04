async function loadVariables() {

    const res = await fetch(`/variables`)
    const data = await res.json()

    const container = document.getElementById("variables-list")

    container.innerHTML = ""

    for (const script in data.scripts) {

        const vars = data.scripts[script]

        for (const name in vars) {

            const item = document.createElement("div")

            item.innerHTML = `
            <label>
            <input type="checkbox" data-script="${script}" data-name="${name}">
            ${name}
            </label>
            `

            container.appendChild(item)
        }
    }

}

document.addEventListener("change", function (e) {

    if (e.target.type === "checkbox") {

        const script = e.target.dataset.script
        const name = e.target.dataset.name

        if (e.target.checked) {

            createWidget(script, name)

        }

    }

})

function createWidget(script, name) {

    const canvas = document.getElementById("dashboard-canvas")

    const widget = document.createElement("div")

    widget.className = "widget"

    widget.style.left = "100px"
    widget.style.top = "100px"
    widget.style.width = "400px"
    widget.style.height = "300px"

    widget.innerHTML = `

    <div class="widget-header">${name}</div>

    <div class="widget-content" id="content-${name}"></div>

    `

    canvas.appendChild(widget)

    makeDraggable(widget)

    loadWidgetData(script, name)

}

async function loadWidgetData(script, name) {

    const res = await fetch(`/variables`)
    const meta = await res.json()

    const item = meta.scripts[script][name]

    const path = item.path

    const dataRes = await fetch(`/data?file_path=${path}`)

    const content = document.getElementById(`content-${name}`)

    if (item.type === "figure") {

        const img = document.createElement("img")
        img.src = `/data?project_root=${projectRoot}&file_path=${path}`
        img.style.width = "100%"

        content.appendChild(img)

    }

    else {

        const data = await dataRes.json()

        renderWidgetContent(content, item.type, data)

    }

}

function renderWidgetContent(container, type, data) {

    if (type === "kpi") {

        container.innerHTML = `<h1>${data.value}</h1>`

    }

    else if (type === "list") {

        container.innerHTML = "<ul>" +
            data.map(v => `<li>${v}</li>`).join("") +
            "</ul>"

    }

    else if (type === "dict") {

        container.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`

    }

    else if (type === "dataframe") {

        const table = document.createElement("table")

        const header = document.createElement("tr")

        data.columns.forEach(c => {

            const th = document.createElement("th")
            th.innerText = c
            header.appendChild(th)

        })

        table.appendChild(header)

        data.rows.forEach(row => {

            const tr = document.createElement("tr")

            data.columns.forEach(c => {

                const td = document.createElement("td")
                td.innerText = row[c]

                tr.appendChild(td)

            })

            table.appendChild(tr)

        })

        container.appendChild(table)

    }

}

function makeDraggable(widget) {

    const header = widget.querySelector(".widget-header")

    let offsetX = 0
    let offsetY = 0

    header.addEventListener("mousedown", function (e) {

        offsetX = e.clientX - widget.offsetLeft
        offsetY = e.clientY - widget.offsetTop

        function move(e) {

            widget.style.left = (e.clientX - offsetX) + "px"
            widget.style.top = (e.clientY - offsetY) + "px"

        }

        function stop() {

            document.removeEventListener("mousemove", move)
            document.removeEventListener("mouseup", stop)

        }

        document.addEventListener("mousemove", move)
        document.addEventListener("mouseup", stop)

    })

}

loadVariables()