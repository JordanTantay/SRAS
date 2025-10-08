(function(){
  const STORAGE_KEY = "cozyThemeEnabled";

  function getCozyLink(){
    const links = document.querySelectorAll('link[rel="stylesheet"]');
    for(const link of links){
      if(link.href.includes('/static/cozy-dark.css')) return link;
    }
    return null;
  }

  function setEnabled(enabled){
    const link = getCozyLink();
    if(link){
      link.disabled = !enabled;
    }
    try{ localStorage.setItem(STORAGE_KEY, enabled ? '1' : '0'); }catch(e){}
    updateButtons(enabled);
  }

  function updateButtons(enabled){
    document.querySelectorAll('[data-theme-toggle]').forEach(function(btn){
      btn.textContent = enabled ? '☀️ Light' : '🌙 Dark';
      btn.setAttribute('aria-pressed', String(enabled));
      btn.classList.toggle('btn-outline-primary', !enabled);
      btn.classList.toggle('btn-outline-light', enabled);
    });
  }

  function init(){
    const saved = (function(){
      try{ return localStorage.getItem(STORAGE_KEY) === '1'; }catch(e){ return true; }
    })();

    // Ensure stylesheet exists; if not, do nothing gracefully
    const link = getCozyLink();
    if(link){ link.disabled = !saved; }

    updateButtons(saved);

    document.addEventListener('click', function(e){
      const t = e.target.closest('[data-theme-toggle]');
      if(!t) return;
      e.preventDefault();
      const current = !(getCozyLink() && getCozyLink().disabled);
      setEnabled(!current);
    });
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  }else{
    init();
  }
})();
