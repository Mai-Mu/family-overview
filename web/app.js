const $ = (s, root = document) => root.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paths = {
 home:'m3 10 9-7 9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V10Zm6 11v-8h6v8',
 grid:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
 book:'M4 4h13a3 3 0 0 1 3 3v14H7a3 3 0 0 1-3-3V4Zm0 13h16M8 8h8M8 11h5',
 repeat:'m17 2 4 4-4 4M3 11V8a2 2 0 0 1 2-2h16M7 22l-4-4 4-4m14-1v3a2 2 0 0 1-2 2H3',
 wallet:'M20 8V5a2 2 0 0 0-2-2L4 6v13a2 2 0 0 0 2 2h14V8H5m15 5h-5v4h5M4 6v3',
 bank:'m3 9 9-6 9 6H3Zm2 3v7m5-7v7m4-7v7m5-7v7M3 22h18',
 arrowup:'m6 15 6-6 6 6M12 9v12M5 3h14',
 arrowdown:'m6 9 6 6 6-6M12 15V3M5 21h14',
 users:'M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2m21 0v-2a4 4 0 0 0-3-3.87M12 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Zm4-3.87a4 4 0 0 1 0 7.75',
 shield:'m12 3 8 3v6c0 5-8 10-8 10S4 17 4 12V6l8-3Zm-4 9 3 3 5-6',
 link:'M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2m3 6a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2',
 plus:'M12 5v14M5 12h14', search:'m21 21-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z',
 chevron:'m9 5 7 7-7 7', close:'m6 6 12 12M6 18 18 6', check:'m5 12 4 4L19 6',
 download:'M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4', file:'M14 2H5v20h14V7l-5-5Zm0 0v6h6M8 13h7m-7 4h5',
 clock:'M12 7v5l3 3M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',
 menu:'M4 6h16M4 12h16M4 18h16', info:'M12 11v6m0-10v1M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',
 trash:'M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7',
 leaf:'M20 3C7 1 1 10 6 16s16 2 14-13ZM5 21l11-13', upload:'M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6',
 save:'M5 3h12l4 4v14H3V3h2Zm2 0v6h10V3M7 21v-8h10v8', lock:'M6 11h12v10H6V11Zm3 0V7a3 3 0 1 1 6 0v4',
};
function icon(name, size=18) { return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name] || paths.book}"/></svg>`; }
const meta = {
 commitments:{name:'重大与约定',icon:'book',short:'家庭约定',subtitle:'一起商量的重要开销，和每个人的承担安排。'},
 recurring_rules:{name:'定期收支',icon:'repeat',short:'定期收支',subtitle:'把工资、月供与日常固定费用，整理成长期规则。'},
 assets:{name:'资产盘点',icon:'wallet',short:'资产',subtitle:'逐项记清家底，金额以最近一次确认的日期为准。'},
 liabilities:{name:'负债与借款',icon:'bank',short:'负债',subtitle:'理清欠款、还款安排，以及实际承担的人。'},
 receivables:{name:'借出款',icon:'arrowup',short:'借出款',subtitle:'记录借出去的钱、归属与约定收回时间。'},
 guarantees:{name:'担保责任',icon:'link',short:'担保',subtitle:'单独记清可能承担的责任和相关约定。'},
 protection:{name:'养老与保障',icon:'shield',short:'保障',subtitle:'养老、医保与商业保险的关键信息，放在一处。'},
 members:{name:'家庭成员',icon:'users',short:'成员',subtitle:'从我、父亲、母亲开始，分别记录，共同商量。'},
};
const nameKeys = {members:'display_name',assets:'asset_name',liabilities:'liability_name',receivables:'receivable_name',guarantees:'guarantee_name',recurring_rules:'rule_name',commitments:'title',protection:'protection_name'};
const amountKeys = {assets:'value',liabilities:'remaining_principal',receivables:'remaining_amount',guarantees:'exposure_amount',recurring_rules:'expected_amount',commitments:'total_amount',protection:'premium_amount'};
const memberKeys = {members:[],assets:['owner_ids'],liabilities:['borrower_ids','payer_ids'],receivables:['owner_ids'],guarantees:['guarantor_ids'],recurring_rules:['income_owner_ids','payer_ids'],commitments:['involved_member_ids','payer_ids'],protection:['covered_member_ids']};
const timeKeys = {assets:'value_as_of',liabilities:'maturity_on',receivables:'expected_return_on',guarantees:'ends_on',recurring_rules:'schedule_note',commitments:'planned_start',protection:'ends_on',members:'work_status'};
const state = {schema:null, records:[], summary:null, module:'overview', member:'', currency:'', search:'', status:'', removed:false};
let detail = null, toastTimer, lastFocus, activeConfirm;
function ask(titleText,message,acceptText='放弃更改') {
 if(activeConfirm)return Promise.resolve(false);
 return new Promise(resolve=>{
  const layer=document.createElement('div');layer.className='confirm-layer';
  layer.innerHTML=`<section class="confirm-card" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title"><div class="empty-icon">${icon('info',22)}</div><h2 id="confirm-title">${esc(titleText)}</h2><p>${esc(message)}</p><div class="confirm-actions"><button class="btn" data-answer="no">返回</button><button class="btn primary" data-answer="yes">${esc(acceptText)}</button></div></section>`;
  const finish=answer=>{layer.remove();activeConfirm=null;resolve(answer);};
  activeConfirm={finish,layer};layer.addEventListener('click',e=>{const button=e.target.closest('[data-answer]');if(button)finish(button.dataset.answer==='yes');});
  document.body.append(layer);layer.querySelector('button')?.focus();
 });
}
function cacheDraft(){try{if(detail?.dirty)localStorage.setItem('family-unsaved-draft',JSON.stringify({module:detail.module,id:detail.record?.id,version:detail.record?.version,draft:detail.draft,child:detail.child,childVersion:detail.childVersion,files:detail.files.length}));}catch{}}
function clearDraftCache(){try{localStorage.removeItem('family-unsaved-draft');}catch{}}

async function api(path, options={}) {
  const headers = options.body instanceof FormData ? {} : {'Content-Type':'application/json'};
  let response;
  try { response = await fetch(path, {...options, headers:{...headers,...options.headers}}); }
  catch { throw new Error('无法连接本地服务，请确认启动窗口仍在运行。'); }
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || '操作未完成，请重试');
  return value;
}
const schema = key => state.schema.modules.find(m=>m.key===key);
const all = module => state.records.filter(r=>r.module===module && !r.deleted_at);
const record = id => state.records.find(r=>r.id===id);
const title = r => r?.data[nameKeys[r.module]] || (r?.module==='members' ? r?.data.family_role : '') || `未命名${meta[r?.module]?.short || '记录'}`;
const members = () => all('members');
const memberName = id => title(record(id));
const isEmpty = v => v===null || v===undefined || v==='' || (Array.isArray(v)&&!v.length);
const shown = v => isEmpty(v) ? '—' : String(v);
const clone = x => structuredClone(x);
const get = (obj,path) => path.split('.').reduce((v,k)=>v?.[k],obj);
function set(obj,path,value) { const keys=path.split('.'); const last=keys.pop(); let at=obj; for(const k of keys) { if(at[k]===null||at[k]===undefined) at[k]={}; at=at[k]; } at[last]=value; }
function number(v) { if(v===null||v===undefined||String(v).trim()==='')return null; const n=Number(String(v).replaceAll(',','')); return Number.isFinite(n)?n:null; }
function numeric(v) { const n=number(v); return n===null?'—':new Intl.NumberFormat('zh-CN',{maximumFractionDigits:2}).format(n); }
function money(v,currency='',symbols=true) {
  if(v===null||v===undefined||v==='')return '—';
  let lo,hi;
  if(typeof v==='object') { const exact=number(v.value); lo=exact!==null?exact:number(v.lower); hi=exact!==null?exact:number(v.upper); }
  else lo=hi=number(v);
  if(lo===null&&hi===null)return '—';
  const text=lo===hi?numeric(lo):lo===null?`不高于 ${numeric(hi)}`:hi===null?`不低于 ${numeric(lo)}`:`${numeric(lo)} – ${numeric(hi)}`;
  const symbol={CNY:'¥',USD:'$',HKD:'HK$',EUR:'€',GBP:'£',JPY:'JP¥'}[currency]||currency;
  return (symbols&&symbol?symbol+' ':'')+text;
}
function dateText(value) { if(!value)return '尚未填写'; try{return new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Hong_Kong',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(value));}catch{return value;} }
function fieldValue(f,value) {
 if(isEmpty(value))return '—';
 if(f.type==='reference')return title(record(value));
 if(f.type==='references')return value.map(memberName).join('、');
 if(f.type==='money_or_range'||f.type==='money')return money(value,'',false);
 if(f.type==='allocation_rows')return value.map(a=>[a.member_id?memberName(a.member_id):'成员待定',a.amount?numeric(a.amount):'',a.percentage?a.percentage+'%':'',a.agreement_note||''].filter(Boolean).join(' ')).join('；');
 return typeof value==='object'?JSON.stringify(value):String(value);
}
function badge(value) { const c=['已约定','已核实','生效','保障有效','已完成','正常履约','领取中','在缴'].includes(value)?'green':['待商讨','待确认','估算','优先保障'].includes(value)?'amber':['进行中','正常安排'].includes(value)?'blue':'gray';return `<span class="badge ${c}">${esc(value||'待补充')}</span>`; }
function people(r) { return [...new Set((memberKeys[r.module]||[]).flatMap(k=>r.data[k]||[]))]; }
function matchesMember(r) {return !state.member || (r.module==='members'?r.id===state.member:people(r).includes(state.member));}
function toast(message,error=false) {clearTimeout(toastTimer);$('#toast-root').innerHTML=`<div class="toast ${error?'error':''}">${icon(error?'info':'check',16)}<span>${esc(message)}</span></div>`;toastTimer=setTimeout(()=>$('#toast-root').innerHTML='',error?6500:3400);}
async function load() {const s=await api('/api/state');state.records=s.records;state.summary=s.summary;if(state.member){state.summary=await api('/api/summary?member_id='+encodeURIComponent(state.member));} }
function navButton(key,label) {return `<button class="nav-item ${state.module===key?'active':''}" data-nav="${key}">${icon(meta[key]?.icon||'grid')}<span>${label||meta[key].name}</span></button>`;}
function shell() {
 $('#app').innerHTML=`<div class="mobile-backdrop" data-action="menu"></div><aside class="sidebar"><div class="brand"><div class="brand-logo">${icon('home',23)}</div><div><strong>家庭一览</strong><small>FAMILY OVERVIEW</small></div></div><nav>${navButton('overview','家庭总览')}<div class="nav-label">家庭安排</div>${navButton('commitments')}${navButton('recurring_rules')}<div class="nav-label">家底资料</div>${['assets','liabilities','receivables','guarantees','protection','members'].map(k=>navButton(k)).join('')}</nav><div class="sidebar-bottom"><div class="local-note"><span class="dot"></span>本地保存 · 仅在这台电脑</div><div class="profile"><span class="avatar">家</span><div><strong>我的家庭</strong><small>共同商讨，统一记录</small></div></div></div></aside><main class="main"><header class="topbar"><div class="breadcrumb"><button class="icon-btn mobile-menu" data-action="menu" aria-label="打开导航">${icon('menu')}</button><span>我的家庭</span>${icon('chevron',12)}<span>${state.module==='overview'?'家庭总览':meta[state.module].name}</span></div><div class="top-actions"><span class="date-label">${new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'long',day:'numeric',weekday:'long'}).format(new Date())}</span><a class="icon-btn" href="/design/家庭经济信息收集字段设计.html" target="_blank" rel="noopener" aria-label="查看字段说明" title="字段说明">${icon('info',17)}</a><button class="btn" data-action="backup">${icon('download',14)}备份数据</button></div></header><div class="content" id="content"></div></main>`;
 renderContent();
}
function switcher() {return `<div class="member-switch" aria-label="按成员查看"><button class="${!state.member?'active':''}" data-member="">全家</button>${members().map(m=>`<button class="${state.member===m.id?'active':''}" data-member="${m.id}">${esc(title(m))}</button>`).join('')}</div>`;}
function empty(iconName,heading,description,button='',action='') {return `<div class="empty"><div class="empty-icon">${icon(iconName,25)}</div><h3>${heading}</h3><p>${description}</p>${button?`<button class="btn small" ${action}>${icon('plus',13)}${button}</button>`:''}</div>`;}
function overview() {
 const currencies=Object.keys(state.summary.currencies);if(!currencies.includes(state.currency))state.currency=currencies[0]||'';
 const sums=state.summary.currencies[state.currency]||{};
 const items=[['assets','已录资产','wallet','最近盘点值'],['liabilities','已录负债','bank','剩余本金或欠款'],['income','月度预计收入','arrowdown','按有效规则频率折算'],['expense','月度预计支出','arrowup','按有效规则频率折算']];
 const contracts=all('commitments').filter(matchesMember).filter(r=>!['已完成','取消'].includes(r.data.status)).slice(0,5);
 const recent=state.records.filter(r=>!r.deleted_at&&matchesMember(r)).slice(0,4);
 const steps=[['members','建立家庭成员','先从我、父亲、母亲开始'],['assets','盘点当前家底','逐项记下资产和负债'],['recurring_rules','整理定期收支','工资、水电、月供等长期规则'],['commitments','记录家庭约定','一起商量金额和承担安排']];
 return `<div class="page-heading"><div><h1>家庭总览</h1><p>家底有记录，重要的安排有着落。</p></div>${switcher()}</div><section class="hero"><div><div class="eyebrow">A LITTLE CLARITY, TOGETHER</div><h2>把家里的重要安排，<br>放在一起。</h2><p>从一次盘点开始，慢慢理清每个人的责任与计划。</p><button class="btn primary" data-new="commitments">${icon('plus',15)}记录一项家庭约定</button></div><div class="hero-art" aria-hidden="true"><div class="art-circle"></div><div class="note-card"><div class="tiny">OUR FAMILY NOTES</div><div class="note-line"><i>✓</i>一起商量</div><div class="note-line"><i>✓</i>清晰记录</div><div class="note-line"><i>✓</i>从容安排</div></div><div class="art-flower">${icon('leaf',23)}</div></div></section><div style="display:flex;justify-content:flex-end;margin:-10px 0 9px">${currencies.length?`<select class="currency-switch" id="summary-currency" aria-label="汇总币种">${currencies.map(c=>`<option ${c===state.currency?'selected':''}>${esc(c)}</option>`).join('')}</select>`:'<span class="muted" style="font-size:10px">填写金额与币种后显示汇总</span>'}</div><section class="metrics">${items.map(([key,label,ico,foot])=>{const value=money(sums[key],state.currency);return `<article class="metric"><div class="metric-top"><span>${label}</span><span class="metric-icon">${icon(ico,15)}</span></div><div class="metric-value ${value.length>16?'range-value':''}">${esc(value)}</div><div class="metric-foot">${foot}${sums[key]?' · '+sums[key].count+'项':' · 尚无可汇总数据'}</div></article>`;}).join('')}</section>${state.summary.pending_count||state.summary.shared_count?`<div class="warning-note">${icon('info',15)}<span>${state.summary.pending_count?`${state.summary.pending_count} 项记录的信息待补充，尚未参与汇总。`:''}${state.summary.shared_count?` ${state.summary.shared_count} 项共同安排单独列示，未自动平分。`:''}</span></div>`:''}<div class="dashboard-grid"><div class="dashboard-left"><section class="panel"><div class="panel-head"><div><h2>最近的家庭约定</h2><p class="sub">已约定与待商讨的事项，都留个位置</p></div><button class="text-link" data-nav="commitments">全部事项 ${icon('chevron',12)}</button></div>${contracts.length?`<div class="panel-body">${contracts.map(r=>smallRow(r)).join('')}</div>`:empty('book','从第一项约定开始','房贷由谁承担，家电何时添置，或一个尚待商量的计划。','新增家庭约定','data-new="commitments"')}</section><section class="panel" style="margin-top:21px"><div class="panel-head"><h2>最近更新</h2><span class="sub">留住每一次确认</span></div>${recent.length?`<div class="panel-body">${recent.map(r=>smallRow(r,true)).join('')}</div>`:`<div class="panel-body"><p style="color:#a6b1a0;font-size:11px;padding:12px 0 20px">还没有记录。填写并保存后，最近的变化会出现在这里。</p></div>`}</section></div><div class="dashboard-right"><section class="panel"><div class="panel-head"><div><h2>初次整理</h2><p class="sub">一次只填一部分，也很好</p></div><span class="badge green">${steps.filter(([k])=>all(k).length).length} / 4</span></div><div class="panel-body">${steps.map(([k,name,desc],i)=>`<button class="step ${all(k).length?'done':''}" ${k==='members'&&!members().length?'data-action="setup"':`data-nav="${k}"`}><span class="step-number">${all(k).length?'✓':String(i+1).padStart(2,'0')}</span><span class="step-text"><strong>${k==='members'&&!members().length?'建立三位成员':name}</strong><small>${desc}</small></span>${icon('chevron',12)}</button>`).join('')}</div></section><section class="panel" style="margin-top:21px"><div class="panel-head"><h2>资料概况</h2><span class="sub">共 ${state.records.filter(r=>!r.deleted_at).length} 项</span></div><div class="panel-body">${['assets','liabilities','protection'].map(k=>`<button class="step" data-nav="${k}"><span class="row-icon">${icon(meta[k].icon,16)}</span><span class="step-text"><strong>${meta[k].name}</strong></span><span class="row-sub">${all(k).length} 项</span>${icon('chevron',12)}</button>`).join('')}</div></section></div></div><footer class="overview-footer"><span class="quiet-note">${icon('lock',12)}所有字段选填 · 数据保存在本机</span><span>资产按最近盘点值展示，收支为已录规则的估算。</span></footer>`;
}
function smallRow(r,recent=false) {return `<div class="small-row" role="button" tabindex="0" data-open="${r.id}"><span class="row-icon">${icon(meta[r.module].icon,16)}</span><div class="row-main"><div class="row-title">${esc(title(r))}</div><div class="row-sub">${recent?meta[r.module].name+' · '+esc(dateText(r.updated_at)):esc((people(r).map(memberName).join('、')||'承担人待商讨'))}</div></div>${recent?icon('chevron',13):`<div style="text-align:right"><div class="row-amount">${esc(money(r.data[amountKeys[r.module]],r.data.currency))}</div><div style="margin-top:4px">${badge(r.data.status)}</div></div>`}</div>`;}
function filtered() {
 return state.records.filter(r=>r.module===state.module && (!!r.deleted_at===state.removed) && matchesMember(r))
  .filter(r=>!state.search||JSON.stringify(r.data).toLocaleLowerCase().includes(state.search.toLocaleLowerCase()))
  .filter(r=>!state.status||(r.data.status||r.data.verification_status||'待补充')===state.status);
}
function listView() {
 const module=state.module,m=meta[module], rows=filtered();
 const statuses=[...new Set(state.records.filter(r=>r.module===module&&!r.deleted_at).map(r=>r.data.status||r.data.verification_status||'待补充'))];
 const columns=module==='members'?['成员','家庭角色','工作／退休状态','最近更新']:['名称',module==='recurring_rules'?'归属／承担人':module==='protection'?'涉及成员':'归属／承担人',module==='liabilities'?'剩余本金':module==='protection'?'每期缴费':'金额',module==='assets'?'盘点日期':module==='recurring_rules'?'频率／时点':'相关时间','状态'];
 return `<div class="module-intro"><div class="module-title"><h1>${m.name}</h1><p>${m.subtitle}</p></div><button class="btn primary" data-new="${module}">${icon('plus',15)}新增${m.short}</button></div><div class="page-heading" style="margin:0 0 22px">${switcher()}<button class="recycle-toggle ${state.removed?'active':''}" data-action="removed">${state.removed?'返回当前记录':'查看已移除记录'}</button></div><div class="list-toolbar"><div class="filters"><label class="search-box">${icon('search')}<input type="search" id="list-search" value="${esc(state.search)}" placeholder="搜索名称、约定或备注" aria-label="搜索记录"></label><select class="filter-select" id="status-filter" aria-label="筛选状态"><option value="">全部状态</option>${statuses.map(s=>`<option ${state.status===s?'selected':''}>${esc(s)}</option>`).join('')}</select></div><span class="list-count">${state.removed?'已移除':'已记录'} ${rows.length} 项</span></div><div class="list-panel">${rows.length?`<table class="records-table"><thead><tr>${columns.map(c=>`<th>${c}</th>`).join('')}<th></th></tr></thead><tbody>${rows.map(r=>tableRow(r)).join('')}</tbody></table>`:empty(m.icon,state.search||state.status?'没有找到匹配记录':state.removed?'还没有移除的记录':`还没有${m.short}记录`,state.search||state.status?'试试调整搜索或筛选条件。':'先记下已知的信息，不清楚的留空，随时保存。',state.search||state.status||state.removed?'':`新增${m.short}`,`data-new="${module}"`)}</div><p class="module-help">${icon('info',13)}${module==='recurring_rules'?'规则用于估算，不会自动登记实际到账或付款。':module==='assets'?'金额对应最近盘点日期，发生重大变化时再更新。':module==='commitments'?'金额不限；已预留与已支付分开记录，尚未商定的先留作待商讨。':'所有字段均可留空。信息不完整也可以先保存为草稿。'}</p>`;
}
function tableRow(r) {
 let cells;
 if(r.module==='members') cells=[`<span class="name-cell">${esc(title(r))}</span>`,esc(shown(r.data.family_role)),esc(shown(r.data.work_status)),esc(dateText(r.updated_at))];
 else cells=[`<span class="name-cell"><span><i class="table-icon">${icon(meta[r.module].icon,15)}</i>${esc(title(r))}</span></span>`,esc(people(r).map(memberName).join('、')||'—'),esc(money(r.data[amountKeys[r.module]],r.data.currency)),esc(r.module==='recurring_rules'?[r.data.frequency,r.data.schedule_note].filter(Boolean).join(' · ')||'—':shown(r.data[timeKeys[r.module]])),badge(r.data.status||r.data.verification_status)];
 return `<tr tabindex="0" data-open="${r.id}" aria-label="打开${esc(title(r))}">${cells.map(c=>`<td>${c}</td>`).join('')}<td>${icon('chevron',13)}</td></tr>`;
}
function renderContent() {$('#content').innerHTML=state.module==='overview'?overview():listView();}
async function navigate(module) {if(!await closeDetail())return;state.module=module;state.search='';state.status='';state.removed=false;shell();window.scrollTo({top:0});}
function refreshList() {const input=$('#list-search'),pos=input?.selectionStart;renderContent();if(input){const next=$('#list-search');next?.focus();try{next?.setSelectionRange(pos,pos);}catch{}}}

function blankFields(module) {return Object.fromEntries([...schema(module).fields,...state.schema.shared_fields].map(f=>[f.key,null]));}
function openRecord(id) {const r=record(id);if(r)openDetail(r.module,r);}
async function openDetail(module,r=null,preset=null) {
 if(detail?.saving)return;
 if(detail?.dirty&&!await ask('有未保存的更改','当前内容尚未保存。返回可以继续填写，或放弃更改打开另一条记录。'))return;
 if(detail?.dirty)clearDraftCache();
 lastFocus=document.activeElement;
 const linked=r?.data.linked_commitment_id?record(r.data.linked_commitment_id):null;
 detail={module,record:r,draft:r?clone(r.data):{...blankFields(module),...(preset||{})},dirty:false,files:[],tab:'form',saving:false,rangeModes:{},amountStash:{},child:linked?clone(linked.data):blankFields('commitments'),childVersion:linked?.version};
 renderDetail();document.body.style.overflow='hidden';
 setTimeout(()=>$('.drawer .icon-btn')?.focus(),0);
}
async function closeDetail() {if(detail?.saving)return false;if(detail?.dirty&&!await ask('有未保存的更改','当前内容尚未保存。返回可以继续填写，或放弃本次更改。'))return false;if(detail)clearDraftCache();detail=null;$('#overlay-root').innerHTML='';document.body.style.overflow='';lastFocus?.focus();return true;}
function dataFor(path) {return path.startsWith('loan.')?detail.child:detail.draft;}
function pathKey(path) {return path.startsWith('loan.')?path.slice(5):path;}
function current(path) {return get(dataFor(path),pathKey(path));}
function update(path,value) {set(dataFor(path),pathKey(path),value);detail.dirty=true;cacheDraft();updateSaveStatus();}
function updateSaveStatus() {const el=$('.save-status');if(el)el.textContent=detail.dirty?'有未保存的更改':detail.record?'已保存 · '+dateText(detail.record.updated_at):'可随时保存，全部选填';}
function updateWarnings() {
 if(!detail)return;
 for(const box of document.querySelectorAll('.drawer [data-field-key]')){
  const path=box.dataset.fieldKey,key=pathKey(path),f=schema(path.startsWith('loan.')?'commitments':detail.module).fields.find(f=>f.key===key)||state.schema.shared_fields.find(f=>f.key===key);
  if(!f)continue;
  const value=current(path);let message='';
  if(!isEmpty(value)){
   if(['money','decimal','percentage','integer','year'].includes(f.type)&&number(value)===null)message='这里需要数字；不确定时可留空，也可以先保存草稿。';
   if(f.type==='money_or_range'){
    const values=typeof value==='object'?value:{value};
    if(Object.values(values).some(v=>!isEmpty(v)&&number(v)===null))message='金额需要数字；不确定的边界可以留空。';
    else if(number(values.lower)!==null&&number(values.upper)!==null&&number(values.lower)>number(values.upper))message='下限大于上限，请核对；仍可先保存草稿。';
   }
   if(f.type==='percentage'&&number(value)!==null&&(number(value)<0||number(value)>100))message='比例超出0–100%，请核对。';
   if(f.type==='partial_date'){
    const m=String(value).match(/^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$/);
    if(!m||(m[2]&&(Number(m[2])<1||Number(m[2])>12))||(m[3]&&(Number(m[3])<1||Number(m[3])>new Date(Date.UTC(Number(m[1]),Number(m[2]),0)).getUTCDate())))message='可填写年、年-月或年-月-日；其他时间安排请写在说明中。';
   }
  }
  box.querySelector('.validation-note')?.remove();
  if(message){const note=document.createElement('p');note.className='validation-note';note.textContent=message;box.append(note);}
 }
}
function fieldHtml(f,values,prefix='') {
 const key=prefix+f.key,v=values[f.key],full=['long_text','references','allocation_rows','money_or_range'].includes(f.type);
 const label=`<label class="field-label" for="f-${esc(key)}">${esc(f.label)}</label>`;
 const note=f.note?`<div class="field-note">${esc(f.note)}</div>`:'';
 let input='';
 if(f.type==='choice')input=`<select id="f-${esc(key)}" data-field="${esc(key)}"><option value="">暂不填写</option>${f.options.map(o=>`<option value="${esc(o)}" ${v===o?'selected':''}>${esc(o)}</option>`).join('')}</select>`;
 else if(f.type==='reference')input=`<select id="f-${esc(key)}" data-field="${esc(key)}"><option value="">暂不关联</option>${all(f.references).map(r=>`<option value="${r.id}" ${v===r.id?'selected':''}>${esc(title(r))}</option>`).join('')}</select>`;
 else if(f.type==='references')input=`<div class="choice-row" role="group" aria-label="${esc(f.label)}">${all(f.references).map(r=>`<button type="button" class="choice-chip ${(v||[]).includes(r.id)?'selected':''}" aria-pressed="${(v||[]).includes(r.id)}" data-multi="${esc(key)}" data-value="${r.id}"><span class="chip-check">✓</span>${esc(title(r))}</button>`).join('')||'<span class="field-note">暂时没有可选记录，可以留空，建立后再关联。</span>'}</div>`;
 else if(f.type==='long_text')input=`<textarea id="f-${esc(key)}" data-field="${esc(key)}" placeholder="按已知情况填写，稍后再补充也可以">${esc(v)}</textarea>`;
 else if(f.type==='money_or_range'){
  const value=typeof v==='object'&&v?v:{value:v??null};
  const mode=detail.rangeModes[key]||(value.value===null&&(value.lower!=null||value.upper!=null)?'range':'single');
  input=`<div class="amount-top">${label}<div class="segmented"><button type="button" data-mode="single" data-key="${esc(key)}" class="${mode==='single'?'active':''}">单一金额</button><button type="button" data-mode="range" data-key="${esc(key)}" class="${mode==='range'?'active':''}">金额范围</button></div></div>${mode==='single'?`<input id="f-${esc(key)}" inputmode="decimal" data-field="${esc(key)}.value" value="${esc(value.value)}" placeholder="金额未确定可留空">`:`<div class="range-inputs"><input id="f-${esc(key)}" inputmode="decimal" data-field="${esc(key)}.lower" value="${esc(value.lower)}" placeholder="下限"><span>至</span><input inputmode="decimal" aria-label="${esc(f.label)}上限" data-field="${esc(key)}.upper" value="${esc(value.upper)}" placeholder="上限"></div>`}`;
 }
 else if(f.type==='allocation_rows'){
  input=`${(v||[]).map((a,i)=>`<div class="allocation"><div class="allocation-grid"><select aria-label="承担人" data-field="${esc(key)}.${i}.member_id"><option value="">成员待定</option>${members().map(m=>`<option value="${m.id}" ${a.member_id===m.id?'selected':''}>${esc(title(m))}</option>`).join('')}</select><input inputmode="decimal" aria-label="承担金额" data-field="${esc(key)}.${i}.amount" value="${esc(a.amount)}" placeholder="金额选填"><input inputmode="decimal" aria-label="承担比例" data-field="${esc(key)}.${i}.percentage" value="${esc(a.percentage)}" placeholder="比例 %"><button class="icon-btn" type="button" data-remove-share="${esc(key)}" data-index="${i}" aria-label="移除这条分担">${icon('close',12)}</button></div><input class="allocation-note" data-field="${esc(key)}.${i}.agreement_note" value="${esc(a.agreement_note)}" placeholder="分担说明，可只写文字约定"></div>`).join('')}<button type="button" class="allocation-add" data-add-share="${esc(key)}">＋ 添加一位承担人</button>`;
 }
 else {
  const placeholders={partial_date:'例如 2026、2026-10 或 2026-10-25',currency:'如 CNY（人民币）',money:'金额未确定可留空',percentage:'百分比，可留空',integer:'可留空',year:'例如 1970'};
  input=`<input id="f-${esc(key)}" data-field="${esc(key)}" ${['money','decimal','percentage','integer','year'].includes(f.type)?'inputmode="decimal"':''} ${f.type==='currency'?'list="currency-options"':''} value="${esc(v)}" placeholder="${esc(placeholders[f.type]||'可留空')}" autocomplete="off">`;
 }
 return `<div class="field ${full?'full':''}" data-field-key="${esc(key)}" data-visibility="${esc(f.show_when||'')}" ${f.show_when&&!conditionMatches(f,values)?'hidden':''}>${f.type==='money_or_range'?'':label}${input}${note}</div>`;
}
function conditionMatches(f,values){if(!f.show_when)return true;const [key,choice]=f.show_when.split(' == ');return !values[key]||values[key]===choice||!isEmpty(values[f.key]);}
function group(titleText,ico,fields,values,prefix='',note='') {
 const core=fields.filter(f=>f.display!=='展开项'),more=fields.filter(f=>f.display==='展开项');
 return `<section class="form-section"><h3>${icon(ico,15)}${titleText}</h3>${note?`<p class="section-note">${note}</p>`:''}<div class="field-grid">${core.map(f=>fieldHtml(f,values,prefix)).join('')}</div>${more.length?`<details class="more-fields" ${core.length?'':'open'}><summary>展开补充信息 · ${more.length} 项选填</summary><div class="field-grid">${more.map(f=>fieldHtml(f,values,prefix)).join('')}</div></details>`:''}</section>`;
}
function formHtml() {
 const module=detail.module,fields=schema(module).fields,draft=detail.draft;
 let content='<p class="optional-note">'+icon('check',13)+'所有字段选填，已知多少就填多少。</p>';
 if(module==='commitments'){
 const groups=[['基本情况','book',['title','purpose','spending_pattern','involved_member_ids','status','priority','planned_start','planned_end','timing_note']],['金额与付款进度','wallet',['total_amount','total_amount_basis','currency','confirmed_paid_amount','paid_period_start','paid_as_of','payment_scope_note','remaining_payment','remaining_payment_basis','reserved_amount']],['承担与家庭约定','users',['payer_ids','allocations','external_share_note','agreement_note']],['关联的长期安排','link',['linked_recurring_rule_ids','linked_liability_id']]];
 content+=groups.map(([name,ico,keys])=>group(name,ico,fields.filter(f=>keys.includes(f.key)),draft)).join('');
 }else content+=group(module==='members'?'成员档案':'基本信息',meta[module].icon,fields,draft);
 if(module==='liabilities'){
 const keys=['confirmed_paid_amount','paid_period_start','paid_as_of','payment_scope_note','remaining_payment','remaining_payment_basis','reserved_amount','allocations','agreement_note'];
 content+=group('家庭还款约定与付款进度','book',schema('commitments').fields.filter(f=>keys.includes(f.key)),detail.child,'loan.','按已知累计数记录即可；保存后与这笔贷款关联，不需要再填一份。');
 }
 if(detail.record&&['liabilities','protection'].includes(module)){
 content+=`<div class="related-action"><span>${module==='liabilities'?'把已有还款信息带入定期支出，后续按规则估算。':'把缴费或领取安排带入定期收支。'}</span><button class="btn small" data-action="make-rule">${icon('plus',12)}建立收支规则</button></div>`;
 }
 content+=group('资料与确认','shield',state.schema.shared_fields.filter(f=>f.type!=='attachment_list'),draft);
 const files=detail.record?.attachments||[];
 content+=`<section class="form-section"><h3>${icon('file',15)}相关资料</h3><label class="upload-zone">${icon('upload',23)}<span>选择图片、保单、账单或其他材料</span><small>选填 · 单个文件不超过25MB · 保存时一并上传</small><input type="file" id="attachment-input" multiple></label>${files.map(f=>`<div class="file-item">${icon('file',14)}<a href="/api/attachments/${f.id}" download>${esc(f.filename)}</a><small>${fileSize(f.size)}</small>${icon('download',13)}</div>`).join('')}${detail.files.map((f,i)=>`<div class="file-item pending-file">${icon('file',14)}<span style="flex:1">${esc(f.name)}</span><small>待保存</small><button class="icon-btn" data-remove-file="${i}" aria-label="移除待上传文件">${icon('close',12)}</button></div>`).join('')}</section><datalist id="currency-options"><option value="CNY">人民币</option><option value="HKD">港币</option><option value="USD">美元</option><option value="EUR">欧元</option><option value="JPY">日元</option><option value="GBP">英镑</option></datalist>`;
 return content;
}
function fileSize(size) {return size<1024?size+' B':size<1024*1024?(size/1024).toFixed(1)+' KB':(size/1024/1024).toFixed(1)+' MB';}
function renderDetail() {
 if(!detail)return;
 const r=detail.record;
 $('#overlay-root').innerHTML=`<div class="overlay"><section class="drawer" role="dialog" aria-modal="true" aria-labelledby="detail-title"><header class="drawer-head"><div class="drawer-head-top"><div><div class="drawer-kicker">${meta[detail.module].name} / ${r?'查看与编辑':'新增记录'}</div><h2 id="detail-title">${r?esc(title(r)):'新增'+meta[detail.module].short}</h2></div><button class="icon-btn" data-action="close" aria-label="关闭详情">${icon('close',20)}</button></div><div class="drawer-tabs"><button class="drawer-tab ${detail.tab==='form'?'active':''}" data-tab="form">填写信息</button><button class="drawer-tab ${detail.tab==='history'?'active':''}" data-tab="history">修改记录${r?'':' · 保存后可查看'}</button></div></header><div class="drawer-body" id="detail-body">${detail.tab==='form'?formHtml():'<p class="optional-note">正在读取修改记录…</p>'}</div><footer class="drawer-footer"><div>${r?`<button class="btn ghost small ${r.deleted_at?'':'danger'}" data-action="${r.deleted_at?'restore':'remove'}">${icon(r.deleted_at?'repeat':'trash',13)}${r.deleted_at?'恢复记录':'移除'}</button>`:''}<span class="save-status"></span></div><div class="actions"><button class="btn" data-action="close">关闭</button>${!r?.deleted_at?`<button class="btn primary" data-action="save" ${detail.saving?'disabled':''}>${icon('save',14)}${detail.saving?'正在保存…':r?'保存修改':'保存草稿'}</button>`:''}</div></footer></section></div>`;
 updateSaveStatus();updateWarnings();if(detail.tab==='history')loadHistory();
}
async function loadHistory() {
 if(!detail.record){$('#detail-body').innerHTML=empty('clock','保存后保留每次修改','可以先保存一份空白草稿，再慢慢补充信息。');return;}
 try{const {history}=await api(`/api/records/${detail.module}/${detail.record.id}/history`);const fields=[...schema(detail.module).fields,...state.schema.shared_fields];
 $('#detail-body').innerHTML=history.map(h=>`<article class="history-item"><div class="history-title"><span>${esc(h.event)} · 版本 ${h.version}</span><small>${esc(dateText(h.created_at))}</small></div><details><summary>查看这次保存的内容</summary><dl class="history-fields">${fields.filter(f=>!isEmpty(h.data[f.key])).map(f=>`<dt>${esc(f.label)}</dt><dd>${esc(fieldValue(f,h.data[f.key]))}</dd>`).join('')||'<dt>空白草稿</dt><dd>暂未填写业务字段</dd>'}</dl></details></article>`).join('');
 }catch(e){$('#detail-body').innerHTML=`<p class="field-note">${esc(e.message)}</p>`;}
}
async function saveDetail() {
 if(!detail||detail.saving)return;
 detail.saving=true;const button=$('[data-action="save"]');if(button){button.disabled=true;button.textContent='正在保存…';}
 $('.drawer-body').inert=true;$('.drawer-head').inert=true;
 document.querySelectorAll('.drawer-footer button').forEach(node=>node.disabled=true);
 try{
 const payload={data:clone(detail.draft),version:detail.record?.version};
 if(detail.module==='liabilities')payload.linked_commitment={data:clone(detail.child),version:detail.childVersion};
 const saved=await api(`/api/records/${detail.module}${detail.record?'/'+detail.record.id:''}`,{method:detail.record?'PUT':'POST',body:JSON.stringify(payload)});
 detail.record=saved;detail.draft=clone(saved.data);detail.dirty=false;clearDraftCache();
 let uploadError='';
 if(detail.files.length){try{for(const file of [...detail.files]){const form=new FormData();form.append('file',file);await api(`/api/records/${detail.module}/${saved.id}/attachments`,{method:'POST',body:form});detail.files=detail.files.filter(f=>f!==file);}}catch(e){uploadError=e.message;detail.dirty=true;}}
 await load();detail.record=record(saved.id);detail.draft=clone(detail.record.data);
 const child=record(detail.record.data.linked_commitment_id);if(child){detail.child=clone(child.data);detail.childVersion=child.version;}
 detail.saving=false;renderContent();renderDetail();toast(uploadError?'记录已保存，部分附件未上传：'+uploadError:'已保存，随时可以继续补充。',!!uploadError);
 }catch(e){detail.saving=false;renderDetail();toast(e.message,true);}
}
async function makeRule() {
 if(detail.dirty){toast('先保存当前内容，再建立关联规则。');return;}
 const source=detail.record,d=source.data;
 let preset;
 if(source.module==='liabilities'){
  const existing=all('recurring_rules').find(r=>r.data.linked_liability_id===source.id)||record(d.linked_recurring_rule_id);
  if(existing){openRecord(existing.id);return;}
  preset={rule_name:d.liability_name?d.liability_name+'还款':null,direction:'支出',category:d.liability_type==='房贷'?'房贷':'其他还款',expected_amount:clone(d.regular_payment),currency:d.currency,payer_ids:d.payer_ids,frequency:d.payment_frequency,schedule_note:d.payment_schedule,linked_liability_id:source.id,linked_commitment_id:d.linked_commitment_id};
 }else{
  const income=d.protection_type==='养老'&&d.pension_amount!=null;
  const existing=record(income?d.linked_income_rule_id:d.linked_expense_rule_id)||all('recurring_rules').find(r=>r.data.linked_protection_id===source.id&&r.data.direction===(income?'收入':'支出'));
  if(existing){openRecord(existing.id);return;}
  preset={rule_name:d.protection_name?d.protection_name+(income?'领取':'缴费'):null,direction:income?'收入':'支出',category:income?'养老金':'医保或保费',expected_amount:clone(income?d.pension_amount:d.premium_amount),currency:d.currency,income_owner_ids:income?d.covered_member_ids:null,payer_ids:income?null:d.premium_payer_ids,frequency:income?d.pension_frequency:d.premium_frequency,linked_protection_id:source.id};
 }
 openDetail('recurring_rules',null,preset);toast('已带入现有信息，确认规则后保存即可。');
}
async function backup() {
 const btn=$('[data-action="backup"]');btn.disabled=true;
 try{const response=await fetch('/api/backup');if(!response.ok)throw new Error('备份未完成，请重试');const blob=await response.blob();const href=URL.createObjectURL(blob);const a=document.createElement('a');a.href=href;a.download='家庭一览备份-'+new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Hong_Kong'}).format(new Date())+'.zip';a.click();setTimeout(()=>URL.revokeObjectURL(href),30000);toast('备份已生成，包含数据库和相关附件。');}catch(e){toast(e.message,true);}finally{btn.disabled=false;}
}
document.addEventListener('input',e=>{
 const target=e.target;
 if(target.id==='list-search'){state.search=target.value;refreshList();return;}
 if(target.dataset.field&&detail){update(target.dataset.field,target.value===''?null:target.value);updateWarnings();}
});
document.addEventListener('change',async e=>{
 const t=e.target;
 try{
 if(t.id==='status-filter'){state.status=t.value;renderContent();}
 else if(t.id==='summary-currency'){state.currency=t.value;renderContent();}
 else if(t.id==='attachment-input'&&detail){const files=[...t.files];if(files.some(f=>f.size>25*1024*1024)){toast('单个附件请控制在25MB以内。',true);return;}detail.files.push(...files);detail.dirty=true;renderDetail();}
 else if(t.dataset.field&&detail){
  update(t.dataset.field,t.value===''?null:t.value);
  if(t.dataset.field==='linked_commitment_id'&&detail.module==='liabilities'){const child=record(t.value);detail.child=child?clone(child.data):blankFields('commitments');detail.childVersion=child?.version;renderDetail();}
  else if(t.dataset.field==='protection_type'){for(const node of document.querySelectorAll('[data-visibility]')){if(!node.dataset.visibility)continue;const f=schema(detail.module).fields.find(f=>f.key===node.dataset.fieldKey);if(f)node.hidden=!conditionMatches(f,detail.draft);}}
 }
 }catch(err){toast(err.message,true);}
});
document.addEventListener('click',async e=>{
 const b=e.target.closest('button,[data-open]');if(!b)return;
 if(detail?.saving)return;
 try{
 if(b.dataset.nav){await navigate(b.dataset.nav);}
 else if(b.dataset.new){openDetail(b.dataset.new);}
 else if(b.dataset.open){openRecord(b.dataset.open);}
 else if(b.hasAttribute('data-member')){state.member=b.dataset.member;await load();renderContent();}
 else if(b.dataset.multi){const key=b.dataset.multi,v=b.dataset.value,values=[...(current(key)||[])];const i=values.indexOf(v);if(i>=0)values.splice(i,1);else values.push(v);update(key,values.length?values:null);b.classList.toggle('selected',i<0);b.setAttribute('aria-pressed',String(i<0));}
 else if(b.dataset.mode){const key=b.dataset.key;let value=current(key);if(!value||typeof value!=='object')value={value:value??null,lower:null,upper:null};const oldMode=detail.rangeModes[key]||(value.value==null&&(value.lower!=null||value.upper!=null)?'range':'single');detail.amountStash[key]??={};detail.amountStash[key][oldMode]=clone(value);detail.rangeModes[key]=b.dataset.mode;const remembered=detail.amountStash[key][b.dataset.mode];const next=remembered?clone(remembered):b.dataset.mode==='range'?{value:null,lower:value.value,upper:value.value}:{value:value.lower===value.upper?value.lower:null,lower:null,upper:null};if(b.dataset.mode==='single'){next.lower=null;next.upper=null;}else next.value=null;update(key,next);renderDetail();}
 else if(b.dataset.addShare){const key=b.dataset.addShare;update(key,[...(current(key)||[]),{member_id:null,amount:null,percentage:null,agreement_note:null}]);renderDetail();}
 else if(b.dataset.removeShare){const key=b.dataset.removeShare,values=[...(current(key)||[])];values.splice(Number(b.dataset.index),1);update(key,values.length?values:null);renderDetail();}
 else if(b.hasAttribute('data-remove-file')){detail.files.splice(Number(b.dataset.removeFile),1);renderDetail();}
 else if(b.dataset.tab){detail.tab=b.dataset.tab;renderDetail();}
 else if(b.dataset.action==='close'){await closeDetail();}
 else if(b.dataset.action==='save'){await saveDetail();}
 else if(b.dataset.action==='make-rule'){await makeRule();}
 else if(b.dataset.action==='menu'){$('.sidebar')?.classList.toggle('open');$('.mobile-backdrop')?.classList.toggle('open');}
 else if(b.dataset.action==='removed'){state.removed=!state.removed;state.status='';renderContent();}
 else if(b.dataset.action==='backup'){await backup();}
 else if(b.dataset.action==='setup'){b.disabled=true;await api('/api/setup-members',{method:'POST',body:'{}'});await load();renderContent();toast('我、父亲、母亲的角色档案已建立，可以随时补充。');}
 else if(['remove','restore'].includes(b.dataset.action)){
  const restore=b.dataset.action==='restore';if(!restore&&!await ask('移除这条记录？','记录移除后不再参与当前汇总，仍可在“已移除记录”中恢复。','移除记录'))return;
  await api(`/api/records/${detail.module}/${detail.record.id}${restore?'/restore':''}`,{method:restore?'POST':'DELETE',...(restore?{body:'{}'}:{})});detail.dirty=false;await closeDetail();await load();renderContent();toast(restore?'记录已恢复。':'记录已移除，可以随时恢复。');
 }
 }catch(err){toast(err.message,true);}
});
document.addEventListener('keydown',e=>{
 if(activeConfirm){if(e.key==='Escape'){e.preventDefault();activeConfirm.finish(false);}if(e.key==='Tab'){const buttons=[...activeConfirm.layer.querySelectorAll('button')];if(e.shiftKey&&document.activeElement===buttons[0]){e.preventDefault();buttons.at(-1).focus();}else if(!e.shiftKey&&document.activeElement===buttons.at(-1)){e.preventDefault();buttons[0].focus();}}return;}
 if(e.key==='Escape'&&detail)closeDetail();
 if(e.key==='Enter'&&e.target.matches('[data-open]'))openRecord(e.target.dataset.open);
 if(e.key==='Tab'&&detail){const nodes=[...document.querySelectorAll('.drawer button:not(:disabled),.drawer input,.drawer select,.drawer textarea,.drawer a,.drawer summary')].filter(el=>el.offsetParent!==null&&!el.closest('[inert]'));if(!nodes.length)return;const first=nodes[0],last=nodes.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}
});
window.addEventListener('beforeunload',cacheDraft);
try{state.schema=await api('/api/schema');await load();shell();let cached;try{cached=JSON.parse(localStorage.getItem('family-unsaved-draft'));}catch{}if(cached&&schema(cached.module)){await openDetail(cached.module,record(cached.id)||null);detail.draft=cached.draft||detail.draft;detail.child=cached.child||detail.child;detail.childVersion=cached.childVersion;if(detail.record&&cached.version)detail.record={...detail.record,version:cached.version};detail.dirty=true;renderDetail();toast(cached.files?'已恢复未保存内容，附件请重新选择。':'已恢复这台浏览器中尚未保存的草稿。');}}
catch(e){$('#app').innerHTML=`<div class="fatal"><div class="empty-icon" style="margin:0 auto 20px">${icon('home',26)}</div><h1>暂时无法打开家庭一览</h1><p>${esc(e.message)}</p><button class="btn primary" onclick="location.reload()">重新连接</button></div>`;}
