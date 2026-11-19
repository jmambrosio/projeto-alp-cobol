'use strict';
const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="app-token"]').content;
const categories = ['Salário','Renda extra','Moradia','Alimentação','Transporte','Saúde','Educação','Lazer','Contas da casa','Compras','Outras receitas','Outras despesas'];
const money = cents => (cents / 100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
const dateText = date => date.split('-').reverse().join('/');
const localDate = () => {const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
let state = null, selectedId = null, toastTimer, loadVersion=0;
const textEl = (tag,cls,text) => {const el=document.createElement(tag); el.className=cls; el.textContent=text; return el;};
async function api(path, options={}) {const response=await fetch(path,{...options,headers:{'X-App-Token':token,'Content-Type':'application/json',...options.headers}}); if(!response.ok){let d;try{d=await response.json();}catch{d={};}throw new Error(d.error || 'Não foi possível concluir. Tente novamente.');}return response;}
function notify(message){clearTimeout(toastTimer);$('toast').textContent=message;$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,4500);}
function rangeQuery(){return `start=${encodeURIComponent($('start').value)}&end=${encodeURIComponent($('end').value)}`;}
function setMonth(){const [y,m]=$('month').value.split('-').map(Number);if(!y||!m)return;$('start').value=`${y}-${String(m).padStart(2,'0')}-01`;$('end').value=`${y}-${String(m).padStart(2,'0')}-${new Date(y,m,0).getDate()}`;}
async function load(){const version=++loadVersion;$('global-error').hidden=true;try{const res=await api('/api/state?'+rangeQuery());const data=await res.json();if(version!==loadVersion)return;state=data;render();}catch(e){if(version===loadVersion){$('global-error').textContent=e.message;$('global-error').hidden=false;}}}
function render(){
  $('demo-banner').hidden=!state.demo;
  for(const id of ['income','expenses','net','balance']){$(id).textContent=money(state[id]);$(id).classList.toggle('negative',state[id]<0);}
  $('balance-date').textContent='Até '+dateText(state.end);
  $('date-range').textContent=dateText(state.start)+' a '+dateText(state.end);
  $('transaction-count').textContent=state.transactions.length;
  const used=state.categories.filter(c=>c.expenses>0).sort((a,b)=>b.expenses-a.expenses);
  $('category-count').textContent=used.length+(used.length===1?' categoria':' categorias');
  $('category-bars').replaceChildren();
  if(!used.length)$('category-bars').append(textEl('p','category-empty','As categorias aparecem aqui quando você registra despesas.'));
  for(const cat of used){const block=document.createElement('div');const line=textEl('div','category-line','');line.append(textEl('span','',cat.name),textEl('span','category-value',money(cat.expenses)+' · '+Math.round(cat.expenses/state.expenses*100)+'%'));const track=textEl('div','track','');const bar=textEl('div','bar','');bar.style.width=(cat.expenses/state.expenses*100)+'%';track.append(bar);block.append(line,track);$('category-bars').append(block);}
  $('insight').textContent=state.transactions.length===0?'Comece registrando suas receitas e despesas.':state.net<0?'As despesas superaram as receitas neste período.':state.income>0?Math.round(state.expenses/state.income*100)+'% das receitas do período foram usadas em despesas.':'Nenhuma receita registrada neste período.';
  renderRows();
}
function renderRows(){if(!state)return;const query=$('search').value.trim().toLocaleLowerCase('pt-BR');const type=$('type-filter').value, cat=$('category-filter').value;const rows=state.transactions.filter(r=>(!type||r.type===type)&&(!cat||r.category===Number(cat))&&r.description.toLocaleLowerCase('pt-BR').includes(query));$('rows').replaceChildren();
  for(const r of rows){const tr=document.createElement('tr'), title=document.createElement('td'),group=textEl('div','entry-type','');group.append(textEl('span','row-symbol '+(r.type==='R'?'income':'expense'),r.type==='R'?'↙':'↗'),textEl('span','entry-title',r.description));title.append(group);const category=document.createElement('td');category.append(textEl('span','tag',categories[r.category-1]));const day=textEl('td','date-cell',dateText(r.date));const amount=textEl('td','amount-cell '+(r.type==='R'?'text-income':'text-expense'),(r.type==='R'?'+ ':'− ')+money(r.cents));const actions=document.createElement('td');const cancel=textEl('button','cancel-row','×');cancel.title='Cancelar lançamento';cancel.setAttribute('aria-label','Cancelar '+r.description);cancel.addEventListener('click',()=>openCancel(r));actions.append(cancel);tr.append(title,category,day,amount,actions);$('rows').append(tr);}
  $('empty').hidden=rows.length>0;$('empty-text').textContent=state.transactions.length?'Nenhum resultado para estes filtros. Tente outra busca.':'Registre sua primeira receita ou despesa para começar.';$('empty-add').hidden=state.transactions.length>0;$('rows-count').textContent=`${rows.length} de ${state.transactions.length} lançamentos`;
}
function categoryOptions(){const type=new FormData($('entry-form')).get('type');const current=$('entry-category').value;$('entry-category').replaceChildren();categories.forEach((name,i)=>{const revenue=[1,2,11].includes(i+1);if((type==='R')===revenue){const option=new Option(name,String(i+1));$('entry-category').add(option);}});if([...$('entry-category').options].some(o=>o.value===current))$('entry-category').value=current;}
function openEntry(){ $('entry-form').reset();$('entry-error').textContent='';$('description-count').textContent='Até 60 bytes; acentos podem ocupar mais espaço.';$('description-count').classList.remove('negative');$('entry-date').value=localDate();categoryOptions();$('entry-dialog').showModal();$('amount').focus();}
function openCancel(row){selectedId=row.id;$('cancel-description').textContent=`${row.description} · ${money(row.cents)} · ${dateText(row.date)}`;$('cancel-error').textContent='';$('cancel-dialog').showModal();}
async function download(path, filename){try{const response=await api(path);const blob=await response.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);}catch(e){notify(e.message);}}
$('month').value=localDate().slice(0,7);setMonth();
categories.forEach((name,i)=>$('category-filter').add(new Option(name,String(i+1))));
$('month').addEventListener('change',()=>{setMonth();load();});
for(const [id,delta] of [['prev-month',-1],['next-month',1]])$(id).addEventListener('click',()=>{const [y,m]=$('month').value.split('-').map(Number);const date=new Date(y,m-1+delta,1);$('month').value=`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}`;setMonth();load();});
$('custom-period').addEventListener('click',()=>{$('period-form').hidden=!$('period-form').hidden;});
$('period-form').addEventListener('submit',e=>{e.preventDefault();$('period-error').textContent='';if($('start').value>$('end').value){$('period-error').textContent='A data final deve ser igual ou posterior à inicial.';return;}load();});
for(const id of ['search','type-filter','category-filter'])$(id).addEventListener('input',renderRows);
for(const id of ['new-entry','empty-add'])$(id).addEventListener('click',openEntry);
document.querySelectorAll('.close-dialog').forEach(el=>el.addEventListener('click',()=>$('entry-dialog').close()));
document.querySelectorAll('.close-cancel').forEach(el=>el.addEventListener('click',()=>$('cancel-dialog').close()));
document.querySelectorAll('input[name="type"]').forEach(el=>el.addEventListener('change',categoryOptions));
$('description').addEventListener('input',()=>{const size=new TextEncoder().encode($('description').value.trim()).length;$('description-count').textContent=`${size}/60 bytes · acentos ocupam mais espaço.`;$('description-count').classList.toggle('negative',size>60);});
$('entry-form').addEventListener('submit',async e=>{e.preventDefault();$('entry-error').textContent='';const data=Object.fromEntries(new FormData(e.currentTarget));data.category=Number(data.category);$('save-entry').disabled=true;try{await api('/api/transactions',{method:'POST',body:JSON.stringify(data)});$('entry-dialog').close();await load();notify(data.date<$('start').value||data.date>$('end').value?'Lançamento salvo. A data está fora do período exibido.':'Lançamento salvo com sucesso.');}catch(error){$('entry-error').textContent=error.message;}finally{$('save-entry').disabled=false;}});
$('confirm-cancel').addEventListener('click',async()=>{$('confirm-cancel').disabled=true;try{await api('/api/cancel',{method:'POST',body:JSON.stringify({id:selectedId})});$('cancel-dialog').close();await load();notify('Lançamento cancelado. Os saldos foram atualizados.');}catch(error){$('cancel-error').textContent=error.message;}finally{$('confirm-cancel').disabled=false;}});
$('export').addEventListener('click',()=>download('/api/export?'+rangeQuery(),'lancamentos.csv'));
$('backup').addEventListener('click',()=>download('/api/backup','lancamentos.dat'));
document.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',()=>{document.querySelectorAll('nav a').forEach(x=>x.classList.toggle('active',x===a));}));
load();
