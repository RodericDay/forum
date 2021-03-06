// Necessary while using DRF Sessions-based Authentication
declare const django:{csrf_token:string; username:string}

const range = n => Array(n).fill(null).map((_,i)=>i+1)
const showtime = timestamp => new Date(timestamp).toISOString().replace(/T/g, ' ').slice(0,-5)
const scrollToId = id => document.getElementById(id).scrollIntoView()
const parenthood = (el:Node, selector:string) => {
    while(el.parentElement&&!el.parentElement.matches(selector)){el=el.parentElement}
    return el.parentElement
}

const escape_ = string => {
    const temp = document.createElement("div")
    temp.textContent = string
    return temp.innerHTML
}
const urlify = string => {
    return string.replace(/(https?:\/\/.[^\s"]+)/g, `<a target="_blank" href="$1">$1</a>`)
}
const quoteindent = string => {
    const lines = string.split('\n')
    const output = []
    const indentation = [0]
    while(lines.length) {
        const line = lines.shift()
        indentation.push( (line.match(/^(&gt;)\1*/, m=>m.length/4)||[''])[0].length/4 )
        let [a, b] = indentation.slice(-2)
        while(a < b) { a++; output.push(`<div class="quote" data-level="${b}">`) }
        while(a > b) { a--; output.push(`</div>`) }
        output.push(line.replace(/^(&gt;)\1*/, m=>`<span class="marker">${m}</span>`)+'\n')
    }
    return output.join('')
}
const markup = (string) => {
    string = escape_(string)
    string = urlify(string)
    string = quoteindent(string)
    return m.trust(string)
}

const url = {
    get root() {return location.href.replace(/\?[\s\S]+/, '')},
    get querystring() {return location.href.replace(/[^\?]+\?/, '')},
    get params() {return m.parseQueryString(url.querystring)},
}

const api = {
    request: (method, headers?) => (url, data?) => m.request({url, method, headers, data}),
    get get() {return this.request('get')},
    get post() {return this.request('post', {"X-CSRFToken": django.csrf_token})},
    get patch() {return this.request('patch', {"X-CSRFToken": django.csrf_token})},
    get delete() {return this.request('delete', {"X-CSRFToken": django.csrf_token})},
}

const state = {
    topics: null,
    posts: null,
    post: null,
    form: {
        title: "",
        text: "",
    },
    users: null,
    errors: [],
    selection: null,
}

const Post = (post, i?) => m(`.post#${post.index}`,
    m(".meta",
        m(".author", Link(`/users/${post.author.id}/`, post.author)),
        m(".timestamp", showtime(post.timestamp)),
        post.context
        ? [
            m(".link", Link(`/topics/${post.topic.id}/posts/?page=${post.context.page}&post=${post.context.index}`, "context")),
            m(".index", `#${post.context.index}`),
        ]
        : [
            m(".link", Link(`/topics/${m.route.param("tid")}/posts/${post.id}/`, "detail")),
            m(".index", `#${post.index||post.id}`),
        ],
    ),
    m(".text", markup(post.text)),
)
const Topic = (topic) => {
    const unseen_count = topic.post_count - topic.seen_count
    return m(".topic",
        m(".posts", Link(`/topics/${topic.id}/posts/`, topic.title)),
        m(".author", Link(`/users/${topic.author.id}/`, topic.author)),
        m(".post-count", topic.post_count),
        m(".unseen-count", unseen_count
        ? Link(`/topics/${topic.id}/posts/?page=${Math.ceil(topic.seen_count/topic.page_size)||1}&post=${topic.seen_count||1}`, `${unseen_count}`)
        : Link(`/topics/${topic.id}/posts/?page=${Math.ceil(topic.post_count/topic.page_size)||1}&post=${topic.post_count||1}`, '')
        ),
        m(".timestamp", showtime(topic.last_post)),
    )
}
const User = (user) => m(".user",
    m(".id", user.id),
    m(".username", user.username),
)
const Link = (href, text) => {
    return m("a", {href, oncreate: m.route.link}, text)
}
const Loading = () => {
    return m(".loading", "Loading...")
}
const Pages = (results) => {
    const N = Math.ceil(results.count/results.page_size)
    return m(".pages",
        range(N).map(i=>(url.params.page||1)==i ? i : m("a", {href: `${url.root}?page=${i}`}, i))
    )
}

const PostReply = {
    async submit(event) {
        event.preventDefault()
        try {
            await api.post(`/api/topics/${m.route.param("tid")}/posts/`, {text: state.form.text})
            state.posts = await api.get(`/api/topics/${m.route.param("tid")}/posts/`)
            state.form.title = ""
            state.form.text = ""
        }
        catch(error) {
            state.errors.push(error)
        }
    },
    oncreate({dom}) {
        document.onkeyup = (e) => {
            if(!dom.open && e.key==='`'){
                dom.open = true
                dom.querySelector("textarea").focus()
            }
        }
    },
    view() {
        return m("details.quickpost", m("summary", "reply"),
            m("form.reply", {onsubmit: this.submit.bind(this)},
                m("textarea", {
                    value: state.form.text,
                    oninput: e=>state.form.text=e.target.value,
                }),
                m("button", "reply"),
            )
        )
    },
}
const PostDetail = {
    async oninit() {
        state.post = null
    },
    async oncreate() {
        state.post = await api.get(`/api/topics/${m.route.param("tid")}/posts/${m.route.param("pid")}/`)
        state.form.text = state.post.text
    },
    async submit() {
        state.post = await api.patch(`/api/topics/${m.route.param("tid")}/posts/${m.route.param("pid")}/`, {text: state.form.text})
        state.form.text = state.post.text
    },
    async delete() {
        state.post = await api.patch(`/api/topics/${m.route.param("tid")}/posts/${m.route.param("pid")}/`, {text: "[deleted]"})
        state.form.text = state.post.text
    },
    view() {
        return m(".post-detail", state.post
            ? [
                m("h1", state.post.topic.title),
                Post(state.post),
                m("form.edit",
                    m("textarea", {oninput: e=>state.form.text=e.target.value, value: state.form.text}),
                ),
                m("button", {onclick: this.submit}, "save changes"),
                m("button", {onclick: this.delete}, "delete"),
            ]
            : [
                Loading()
            ]
        )
    },
}
const PostList = {
    async oninit() {
        state.posts = null
    },
    async oncreate() {
        state.posts = await api.get(`/api/topics/${m.route.param("tid")}/posts/?page=${url.params.page||1}`)
        if(url.params.post) setTimeout(scrollToId, 100, url.params.post)
    },
    async delete() {
        if(!confirm("You sure?")) return
        await api.delete(`/api/topics/${m.route.param("tid")}/`)
        m.route.set('/topics/')
    },
    async highlight() {
        const range = getSelection().getRangeAt(0)
        const {startContainer, endContainer, collapsed} = range
        const post = parenthood(startContainer, ".post")
        if(!post || post !== parenthood(endContainer, ".post") || collapsed) {
            state.selection = null
        }
        else {
            const prefix = ">"
            const midQuote = parenthood(startContainer, ".quote")
            const pad = midQuote ? Array(+midQuote.dataset.level).fill(prefix).join('') : ''
            const text = pad + range.toString().trim().replace(/^/gm, prefix)

            const rects = range.getClientRects()
            const {right:x, bottom:y} = Array.from(rects).pop()
            state.selection = {text, left: `${x}px`, top: `${y}px`}
        }
        m.redraw()
    },
    async quote({target}) {
        // hack to truly deselect on iPhone
        const list = document.querySelector(".post-list")
        list.parentNode["style"].userSelect = "none"
        setTimeout(()=>list.parentNode["style"].userSelect = null, 100)

        state.form.text += state.selection.text + '\n\n'
        document.querySelector(".quickpost")["open"] = true
        const textarea:HTMLTextAreaElement = document.querySelector("form.reply textarea")
        setTimeout(()=>{textarea.scrollTop=1E9; textarea.focus()}, 100)
        state.selection = null
        m.redraw()
    },
    view() {
        document.onselectionchange = this.highlight
        return state.posts
            ? [
                m("h1", state.posts.topic.title),
                m(PostReply),
                m(".post-list", state.posts.results.map(Post)),
                state.selection
                ? m("button#quote", {onclick: this.quote, style: state.selection}, "quote")
                : null,
                Pages(state.posts),
            ]
            : [
                Loading(),
            ]
    },
}
const TopicList = {
    async oncreate() {
        try {
            state.topics = await api.get(`/api/topics/?page=${url.params.page||1}`)
        }
        catch(error) {
            state.errors.push(error)
        }
    },
    view() {
        return state.topics
            ? [
                m("h1", "All Topics"),
                m(".topic-list.table", state.topics.results.map(Topic)),
                Pages(state.topics),
            ]
            : [
                Loading(),
            ]
    },
}
const TopicNew = {
    async submit(event) {
        event.preventDefault()
        try {
            await api.post("/api/topics/", {title: state.form.title, text: state.form.text})
            m.route.set("/topics/")
            state.form.title = ""
            state.form.text = ""
        }
        catch(error) {
            state.errors.push(error)
        }
    },
    view() {
        return [
            m("h1", "New Topic"),
            m("form.topic", {onsubmit: this.submit.bind(state)},
                m("input", {oninput: e=>state.form.title=e.target.value, value: state.form.title}),
                m("textarea", {oninput: e=>state.form.text=e.target.value, value: state.form.text}),
                m("button", "post"),
            ),
        ]
    },
}
const Profile = {
    view() {
        return [
            m("h1", "Profile"),
            m("p", 'Hello ', m("strong", django.username)),
            m("a[href=/logout/]", "log out"),
        ]
    }
}
const UserList = {
    async oninit() {
        state.users = null
    },
    async oncreate() {
        try {
            state.users = await api.get("/api/users/")
        }
        catch(error) {
            state.errors.push(error)
        }
    },
    view() {
        return state.users
        ? [
            m("h1", "User list"),
            m(".user-list.table", state.users.results.map(User)),
        ]
        : [
            Loading(),
        ]
    },
}
const Stats = {
    view() {
        return [
            m("h1", "Site Statistics"),
        ]
    }
}
const Layout = subcomponent => ({
    view() {
        return [
            m("nav",
                Link("/topics/", "Topics"),
                Link("/topics/new/", "New Topic"),
                Link("/profile/", "Profile"),
                Link("/users/", "Users"),
                Link("/stats/", "Stats"),
            ),
            m("main",
                m(subcomponent, {key: location.href}),
                m(".errors", state.errors.map(
                    (error,i) => m("div", {onclick: ()=>state.errors.splice(i, 1)}, Object.keys(error).map(k=>error[k]).join(' '))
                )),
            ),
        ]
    }
})

m.route(document.body, '/topics/', {
    '/topics/': Layout(TopicList),
    '/topics/new/': Layout(TopicNew),
    '/topics/:tid/posts/': Layout(PostList),
    '/topics/:tid/posts/:pid/': Layout(PostDetail),
    '/profile/': Layout(Profile),
    '/stats/': Layout(Stats),
    '/users/': Layout(UserList),
})
