const CATS=['All News','Top Stories','US & Israel','Israeli Politics','Iran & Proxies','Jewish World','Christians & Jews','South Africa & ICJ','Innovation & Good News','Partners Doing Good'];
const $=s=>document.querySelector(s);
let data={articles:[],status:'not_initialized',generated_at:null},cat='All News',savedOnly=false,query='';
const storageKey='iw-bookmarks-v1';
let bookmarks=new Set();try{bookmarks=new Set(JSON.parse(localStorage.getItem(storageKey)||'[]'))}catch{}
const fmt=iso=>iso?new Intl.DateTimeFormat('en-ZA',{timeZone:'Africa/Johannesburg',dateStyle:'medium',timeStyle:'short'}).format(new Date(iso)):'Unknown date';
function notice(message){let el=$('#notice');el.textContent=message;el.classList.toggle('show',!!message)}
function addText(el,text){el.textContent=text||'';return el}
function render(){
 const cats=$('#categories');cats.replaceChildren();
 CATS.forEach(c=>{let b=document.createElement('button');addText(b,c);b.className=cat===c?'active':'';b.onclick=()=>{cat=c;render()};cats.append(b)});
 $('#sectiontitle').textContent=cat;
 $('#sectionhint').textContent=savedOnly?'YOUR BOOKMARKS':cat==='All News'?'LATEST REPORTING':'TOPIC BRIEFING';
 $('#savedtoggle').classList.toggle('active',savedOnly);
 $('#savedcount').textContent=bookmarks.size;
 let list=data.articles.filter(a=>(cat==='All News'||(a.categories||[]).includes(cat))&&(!savedOnly||bookmarks.has(a.url))&&(!query||[a.title,a.source,...(a.categories||[])].join(' ').toLowerCase().includes(query)));
 $('#count').textContent=`${list.length} stories`;
 const grid=$('#articles');grid.replaceChildren();
 if(!list.length){let el=document.createElement('div');el.className='empty';addText(el,data.status==='not_initialized'?'News feeds have not run yet. Publish this app and run the update workflow once to populate headlines.':'No headlines match these filters.');grid.append(el);return}
 list.slice(0,140).forEach(a=>{
  const card=document.createElement('article');card.className='story';
  const top=document.createElement('div');top.className='top';addText(top,(a.categories||[])[0]||'NEWS');
  const title=document.createElement('h3'),link=document.createElement('a');addText(link,a.title);link.href=a.url;link.target='_blank';link.rel='noopener noreferrer';title.append(link);
  const bottom=document.createElement('div');bottom.className='bottom';const details=document.createElement('span');addText(details,`${a.source} · ${fmt(a.published)}`);const star=document.createElement('button');star.className='save';star.setAttribute('aria-label',bookmarks.has(a.url)?'Remove saved article':'Save article');star.title='Save article';addText(star,bookmarks.has(a.url)?'★':'☆');star.onclick=()=>{bookmarks.has(a.url)?bookmarks.delete(a.url):bookmarks.add(a.url);localStorage.setItem(storageKey,JSON.stringify([...bookmarks]));render()};bottom.append(details,star);card.append(top,title,bottom);grid.append(card);
 });
}
async function refresh(){const btn=$('#refresh');btn.disabled=true;btn.textContent='◌';try{const res=await fetch(`./data/news.json?t=${Date.now()}`,{cache:'no-store'});if(!res.ok)throw Error(`HTTP ${res.status}`);data=await res.json();$('#updated').textContent=data.generated_at?fmt(data.generated_at):'Awaiting first feed run';if(data.status==='not_initialized')notice('Initial setup needed: the first news update has not run.');else if(data.status==='failed')notice('All source requests failed during the most recent update. Existing stories may be outdated.');else if(data.status==='partial')notice(`${data.feed_failures?.length||0} source feeds could not be reached. Some stories may be missing.`);else notice('');render()}catch(err){notice(`Could not load the latest news snapshot (${err.message}). Check internet or deployment.`)}finally{btn.disabled=false;btn.textContent='↻'}}
$('#refresh').onclick=refresh;
$('#search').oninput=e=>{query=e.target.value.toLowerCase().trim();render()};
$('#savedtoggle').onclick=()=>{savedOnly=!savedOnly;render()};
if('serviceWorker'in navigator && location.protocol==='https:')navigator.serviceWorker.register('./service-worker.js').catch(()=>{});
render();refresh();setInterval(refresh,15*60*1000);
