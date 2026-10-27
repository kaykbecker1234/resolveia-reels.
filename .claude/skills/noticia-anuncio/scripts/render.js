// Renderizador do modelo de vídeo. Chamado pelo pipeline.py; não precisa ser usado direto.
//   node render.js meta    <roteiro.json>                       -> imprime MARKS/SFX/END em JSON
//   node render.js preview <roteiro.json> <out.jpg>             -> folha de prévia (tempo-base)
//   node render.js frames  <roteiro.json> <timing.json> <dir> [workers]
//   node render.js stills  <roteiro.json> <timing.json> <dir> <t1,t2,...>   (tempo final)
const {chromium} = require('playwright');
const path = require('path'), fs = require('fs');
const TPL = path.resolve(__dirname, '..', 'assets', 'template', 'video.html');

function warp(timing) {
  const A = timing.anchors; // [[base, final], ...]
  return t => {
    for (let i = 1; i < A.length; i++) {
      const [a0, b0] = A[i - 1], [a1, b1] = A[i];
      if (t <= b1) return a0 + (a1 - a0) * Math.max(0, t - b0) / (b1 - b0);
    }
    return A[A.length - 1][0];
  };
}

async function page(browser, data) {
  const p = await browser.newPage({viewport: {width: 1080, height: 1920}});
  await p.addInitScript(d => { window.DATA = d; }, data);
  await p.goto('file://' + TPL);
  await p.evaluate(() => document.fonts.ready);
  return p;
}

(async () => {
  const [mode, roteiro, a3, a4, a5] = process.argv.slice(2);
  const data = JSON.parse(fs.readFileSync(roteiro, 'utf8')).tela || {};
  const browser = await chromium.launch();
  try {
    if (mode === 'meta') {
      const p = await page(browser, data);
      console.log(JSON.stringify(await p.evaluate(() => ({marks: MARKS, scenes: SCENE_STARTS, end: END, tail: TAIL_FROM, sfx: SFX, preview: PREVIEW_AT}))));
    } else if (mode === 'preview') {
      const p = await page(browser, data);
      const times = await p.evaluate(() => PREVIEW_AT);
      const dir = path.dirname(a3) + '/_prev'; fs.mkdirSync(dir, {recursive: true});
      for (let i = 0; i < times.length; i++) {
        await p.evaluate(t => render(t), times[i]);
        await p.screenshot({path: `${dir}/p${String(i).padStart(2, '0')}.jpg`, type: 'jpeg', quality: 80});
      }
      console.log(dir);
    } else if (mode === 'frames') {
      const timing = JSON.parse(fs.readFileSync(a3, 'utf8')), f = warp(timing);
      const fps = 30, n = Math.round(timing.duration * fps), W = +(a5 || 3);
      fs.mkdirSync(a4, {recursive: true});
      await Promise.all(Array.from({length: W}, async (_, w) => {
        const p = await page(browser, data);
        for (let i = w; i < n; i += W) {
          await p.evaluate(t => render(t), f(i / fps));
          await p.screenshot({path: `${a4}/f_${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 90});
        }
      }));
      console.log('frames', n);
    } else if (mode === 'stills') {
      const timing = JSON.parse(fs.readFileSync(a3, 'utf8')), f = warp(timing);
      fs.mkdirSync(a4, {recursive: true});
      const p = await page(browser, data);
      const ts = a5.split(',').map(Number);
      for (let i = 0; i < ts.length; i++) {
        await p.evaluate(t => render(t), f(ts[i]));
        await p.screenshot({path: `${a4}/s${String(i).padStart(2, '0')}.jpg`, type: 'jpeg', quality: 80});
      }
    }
  } finally { await browser.close(); }
})();
