#!/usr/bin/env python3
"""
Molecular 3D Viewer

将 SMILES 字符串或化学名称转换为分子 3D 结构
支持生成 SDF 文件、3D 分子图片和可交互 HTML 网页（可旋转观察）
"""

import argparse
import json
import sys
import base64
import io
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

def import_dependencies():
    global Chem, AllChem, rdMolDescriptors, rdmolfiles, Draw, Descriptors
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem, rdMolDescriptors, rdmolfiles, Draw, Descriptors
    except ImportError:
        print("错误：请安装 rdkit: pip install rdkit", file=sys.stderr)
        sys.exit(1)

import_dependencies()


class PolymerHandler:
    """聚合物 SMILES 处理器"""
    
    def __init__(self):
        pass
    
    def is_polymer_smiles(self, smiles: str) -> bool:
        """检查 SMILES 是否为聚合物"""
        polymer_markers = ['*', '[n]', '[[', ']]']
        return any(marker in smiles for marker in polymer_markers)
    
    def clean_polymer_smiles(self, smiles: str) -> str:
        """清理聚合物 SMILES 以便 RDKit 处理"""
        clean = re.sub(r'\[\*:\d+\]', '[H]', smiles)
        clean = clean.replace('*', '[H]')
        clean = re.sub(r'\[n\]', '', clean)
        clean = clean.replace('[[', '').replace(']]', '')
        return clean if clean else smiles


class Mol3DViewer:
    """分子 3D 可视化器"""
    
    def __init__(self, width: int = 800, height: int = 600, 
                 style: str = 'stick', bg_color: str = 'white',
                 show_labels: bool = True, auto_rotate: bool = False,
                 force_field: str = 'mmff94', max_steps: int = 200):
        self.width = width
        self.height = height
        self.style = style
        self.bg_color = bg_color
        self.show_labels = show_labels
        self.auto_rotate = auto_rotate
        self.force_field = force_field
        self.max_steps = max_steps
        self.polymer_handler = PolymerHandler()
    
    def smiles_to_mol_3d(self, smiles: str) -> Optional[Any]:
        """SMILES 转 3D RDKit Mol 对象（带 3D 坐标优化）"""
        try:
            is_polymer = self.polymer_handler.is_polymer_smiles(smiles)
            if is_polymer:
                smiles = self.polymer_handler.clean_polymer_smiles(smiles)
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            
            mol = Chem.AddHs(mol)
            params = AllChem.ETKDGv3()
            params.randomSeed = 42
            
            result = AllChem.EmbedMolecule(mol, params)
            if result == -1:
                result = AllChem.EmbedMolecule(mol, AllChem.ETKDG())
                if result == -1:
                    return None
            
            try:
                if self.force_field.lower() == 'uff':
                    AllChem.UFFOptimizeMolecule(mol, maxIters=self.max_steps)
                else:
                    AllChem.MMFFOptimizeMolecule(mol, maxIters=self.max_steps)
            except Exception:
                try:
                    AllChem.UFFOptimizeMolecule(mol, maxIters=self.max_steps)
                except Exception:
                    pass
            
            return mol
        except Exception as e:
            print(f"DEBUG smiles_to_mol_3d error: {e}", file=sys.stderr)
            return None
    
    def name_to_smiles(self, name: str) -> Optional[str]:
        """IUPAC 名称转 SMILES（使用 OPSIN API）"""
        try:
            import requests
            url = f"https://opsin.ch.cam.ac.uk/opsin/{requests.utils.quote(name)}"
            response = requests.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict) and data.get("smiles"):
                return data["smiles"]
            elif isinstance(data, dict) and data.get("status") == "SUCCESS":
                import re
                match = re.search(r'<smiles[^>]*>([^<]+)</smiles>', data.get("cml", ""))
                if match:
                    return match.group(1)
            return None
        except Exception as e:
            print(f"DEBUG name_to_smiles error: {e}", file=sys.stderr)
            return None
    
    def save_sdf(self, mol: Any, output_file: str) -> Dict[str, Any]:
        """保存为 SDF 文件"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            writer = rdmolfiles.SDWriter(str(output_file))
            writer.write(mol)
            writer.close()
            
            return {
                "status": "success",
                "output_file": str(output_file),
                "format": "sdf",
                "atoms": mol.GetNumAtoms(),
                "bonds": mol.GetNumBonds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": type(e).__name__,
                "message": str(e)
            }
    
    def generate_html(self, mol: Any, smiles: str, title: str = "Molecule 3D Viewer",
                      input_name: Optional[str] = None) -> str:
        """生成可交互 3D HTML 网页"""
        # 计算分子式和分子量
        try:
            mol_formula = rdMolDescriptors.CalcMolFormula(mol)
            mol_weight = Descriptors.MolWt(mol)
        except Exception as e:
            print(f"DEBUG: 计算分子信息失败：{e}")
            mol_formula = "N/A"
            mol_weight = 0.0
        
        bg_hex = '#ffffff' if self.bg_color == 'white' else self.bg_color
        labels_js = 'viewer.setLabelMode($3Dmol.LabelMode.ALL);' if self.show_labels else ''
        rotate_init = 'true' if self.auto_rotate else 'false'
        labels_btn = '隐藏' if self.show_labels else '显示'
        rotate_btn = '停止' if self.auto_rotate else '启动'
        
        style_map = {
            'stick': "'stick'",
            'sphere': "'sphere'",
            'ball_stick': "{stick: {}, sphere: {scale: 0.3}}",
            'surface': "'surface'",
            'line': "'line'"
        }
        style_config = style_map.get(self.style, "'stick'")
        
        html_template = self._get_html_template()
        
        html = html_template.format(
            title=title,
            width=self.width,
            height=self.height,
            bg_color=bg_hex,
            mol_formula=mol_formula,
            mol_weight=f"{mol_weight:.2f}",
            smiles=smiles[:100] + ('...' if len(smiles) > 100 else ''),
            input_name_section=f'<div class="info-item"><div class="info-label">输入名称</div><div class="info-value">{input_name}</div></div>' if input_name else '',
            sdf_block=Chem.MolToMolBlock(mol),
            style_config=style_config,
            labels_js=labels_js,
            rotate_init=rotate_init,
            labels_btn=labels_btn,
            rotate_btn=rotate_btn,
            download_name=title.replace(' ', '_')
        )
        
        return html
    
    def _get_html_template(self) -> str:
        """返回 HTML 模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px;
    }}
    .container {{
      background: white;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      padding: 20px;
      max-width: 1200px;
      width: 100%;
    }}
    h1 {{ color: #333; margin-bottom: 10px; font-size: 24px; text-align: center; }}
    .info {{
      background: #f8f9fa;
      padding: 15px;
      border-radius: 8px;
      margin-bottom: 15px;
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
      justify-content: center;
    }}
    .info-item {{ flex: 1; min-width: 150px; text-align: center; }}
    .info-label {{ font-size: 12px; color: #666; margin-bottom: 5px; }}
    .info-value {{ font-size: 16px; font-weight: 600; color: #333; }}
    #viewer-container {{
      width: {width}px;
      height: {height}px;
      background: {bg_color};
      border-radius: 8px;
      border: 2px solid #e0e0e0;
      position: relative;
      margin: 20px auto;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .controls {{
      margin-top: 15px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: center;
    }}
    button {{
      padding: 8px 16px;
      border: none;
      border-radius: 6px;
      background: #667eea;
      color: white;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.2s;
    }}
    button:hover {{ background: #5568d3; transform: translateY(-2px); }}
    button:active {{ transform: translateY(0); }}
    .instructions {{
      margin-top: 15px;
      padding: 15px;
      background: #f0f4ff;
      border-radius: 8px;
      font-size: 14px;
      color: #555;
    }}
    .instructions h3 {{ margin-bottom: 10px; color: #667eea; }}
    .instructions ul {{ margin-left: 20px; }}
    .instructions li {{ margin: 5px 0; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>🧪 {title}</h1>
    <div class="info">
      <div class="info-item">
        <div class="info-label">分子式</div>
        <div class="info-value" style="font-size: 20px; color: #667eea;">{mol_formula}</div>
      </div>
      <div class="info-item">
        <div class="info-label">分子量</div>
        <div class="info-value" style="font-size: 20px; color: #764ba2;">{mol_weight} <span style="font-size: 14px;">g/mol</span></div>
      </div>
      <div class="info-item">
        <div class="info-label">SMILES</div>
        <div class="info-value" style="font-family: monospace; font-size: 11px; overflow-x: auto; max-width: 300px;">{smiles}</div>
      </div>
      {input_name_section}
    </div>
    <div id="viewer-container"></div>
    <div class="controls">
      <button onclick="setStyle('stick')">棍状模型</button>
      <button onclick="setStyle('sphere')">空间填充</button>
      <button onclick="setStyle('ball_stick')">球棍模型</button>
      <button onclick="resetView()">重置视角</button>
    </div>
    <div class="instructions">
      <h3>🖱️ 鼠标控制</h3>
      <ul>
        <li><strong>左键拖动</strong> - 旋转分子</li>
        <li><strong>右键拖动</strong> - 平移分子</li>
        <li><strong>滚轮</strong> - 缩放</li>
        <li><strong>双击</strong> - 重置视角</li>
      </ul>
    </div>
  </div>
  <script>
    let viewer = null;
    let isRotating = {rotate_init};
    let rotationFrame = null;
    
    function initViewer() {{
      const element = document.getElementById('viewer-container');
      const config = {{ 
        backgroundColor: '{bg_color}', 
        width: {width}, 
        height: {height}
      }};
      viewer = $3Dmol.createViewer(element, config);
      
      // 添加模型
      viewer.addModel(`{sdf_block}`, "sdf");
      
      // 设置样式
      viewer.setStyle({{}}, {style_config});
      {labels_js}
      
      // 渲染
      viewer.render();
      
      // 关键：等待渲染完成后再 zoomTo
      setTimeout(function() {{
        viewer.zoomTo();
        viewer.render();
        
        // 再次确保视角正确
        setTimeout(function() {{
          viewer.zoom(0.8);
          viewer.render();
          
          // 自动点击重置视角按钮，确保分子显示
          setTimeout(function() {{
            resetView();
          }}, 100);
        }}, 50);
      }}, 100);
      
      if (isRotating) {{ startRotation(); }}
    }}
    
    function setStyle(style) {{
      if (!viewer) return;
      
      let styleConfig;
      switch(style) {{
        case 'stick':
          styleConfig = {{stick: {{}}}};
          break;
        case 'sphere':
          styleConfig = {{sphere: {{scale: 0.3}}}};
          break;
        case 'ball_stick':
          styleConfig = {{stick: {{}}, sphere: {{scale: 0.25}}}};
          break;
        case 'surface':
          styleConfig = {{surface: {{}}}};
          break;
        case 'line':
          styleConfig = {{line: {{}}}};
          break;
        default:
          styleConfig = {{stick: {{}}}};
      }}
      
      viewer.clear();
      viewer.addModel(`{sdf_block}`, "sdf");
      viewer.setStyle({{}}, styleConfig);
      viewer.zoomTo();
      viewer.render();
    }}
    
    function toggleLabels() {{
      if (!viewer) return;
      // 切换标签显示
      const currentLabels = viewer.getLabelsShown();
      viewer.setLabelsShown(!currentLabels);
      viewer.render();
    }}
    
    function toggleRotation() {{
      isRotating = !isRotating;
      if (isRotating) {{ startRotation(); }} else {{ stopRotation(); }}
    }}
    
    function startRotation() {{
      if (!viewer) return;
      function rotate() {{
        if (!isRotating) return;
        viewer.rotate(1, 0, 0);
        viewer.render();
        rotationFrame = requestAnimationFrame(rotate);
      }}
      rotate();
    }}
    
    function stopRotation() {{
      if (rotationFrame) {{ cancelAnimationFrame(rotationFrame); rotationFrame = null; }}
    }}
    
    function resetView() {{ 
      if (!viewer) return; 
      viewer.zoomTo(); 
      viewer.render(); 
    }}
    
    function screenshot() {{
      if (!viewer) return;
      const dataUrl = viewer.pngToImg();
      const link = document.createElement('a');
      link.download = '{download_name}.png';
      link.href = dataUrl;
      link.click();
    }}
    
    window.addEventListener('load', initViewer);
  </script>
</body>
</html>'''
    
    def generate_3d_image(self, mol: Any, output_file: str, format: str = 'png') -> Dict[str, Any]:
        """
        生成真正的 3D 分子图片（球棍模型，有透视和阴影）
        方法：从 3Dmol.js 网页截图
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 生成 SDF 数据
            sdf_block = Chem.MolToMolBlock(mol)
            
            # 创建临时 HTML 用于截图
            temp_html = output_path.with_suffix('.temp_screenshot.html')
            html_content = self._generate_screenshot_html(sdf_block, self.width, self.height)
            temp_html.write_text(html_content, encoding='utf-8')
            
            # 使用 playwright 截图
            try:
                from playwright.sync_api import sync_playwright
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={'width': self.width, 'height': self.height})
                    page.goto(f'file://{temp_html.absolute()}')
                    page.wait_for_timeout(2000)  # 等待渲染和旋转完成
                    page.screenshot(path=str(output_path), type='png')
                    browser.close()
                
                temp_html.unlink()  # 清理临时文件
                
                return {
                    "status": "success",
                    "output_file": str(output_file),
                    "format": format.lower(),
                    "size": f"{self.width}x{self.height}",
                    "type": "real_3d_screenshot"
                }
                
            except ImportError:
                # playwright 未安装，回退到 RDKit 2D
                print("DEBUG: playwright 未安装，使用 RDKit 2D 回退")
                temp_html.unlink()
                return self._generate_2d_fallback(mol, output_file, format)
            
        except Exception as e:
            print(f"DEBUG: 3D 截图失败：{e}，使用 2D 回退")
            return self._generate_2d_fallback(mol, output_file, format)
    
    def _generate_screenshot_html(self, sdf_block: str, width: int, height: int) -> str:
        """生成用于截图的 HTML（纯白背景，球棍模型）"""
        return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Molecule 3D</title>
<style>body{{margin:0;padding:0;background:white;overflow:hidden;}}</style>
</head>
<body>
<div id="container" style="width:{width}px;height:{height}px;"></div>
<script src="https://3Dmol.org/build/3Dmol-min.js"></script>
<script>
(function() {{
  var viewer = $3Dmol.createViewer('container', {{
    bg: 'white',
    width: {width},
    height: {height}
  }});
  viewer.addModel(`{sdf_block}`, "sdf");
  viewer.setStyle({{}}, {{
    stick: {{radius: 0.15, color: 'gray'}},
    sphere: {{scale: 0.25}}
  }});
  viewer.zoomTo();
  viewer.render();
  // 设置一个好看的 3D 视角
  setTimeout(function() {{
    viewer.rotate(45, 'x');
    viewer.rotate(45, 'y');
    viewer.render();
  }}, 300);
}})();
</script>
</body>
</html>'''
    
    def _generate_2d_fallback(self, mol: Any, output_file: str, format: str) -> Dict[str, Any]:
        """回退：使用 RDKit 生成 2D 结构图"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            from rdkit.Chem.Draw import rdMolDraw2D
            
            if format.lower() == 'svg':
                drawer = rdMolDraw2D.MolDraw2DSVG(self.width, self.height)
                drawer.DrawMolecule(mol)
                drawer.FinishDrawing()
                output_path.write_text(drawer.GetDrawingText(), encoding='utf-8')
            else:
                drawer = rdMolDraw2D.MolDraw2DCairo(self.width, self.height)
                opts = drawer.drawOptions()
                opts.bondLineWidth = 3
                opts.highlightBondWidthMultiplier = 5
                drawer.DrawMolecule(mol)
                drawer.FinishDrawing()
                output_path.write_bytes(drawer.GetDrawingText())
            
            return {
                "status": "success",
                "output_file": str(output_file),
                "format": format.lower(),
                "size": f"{self.width}x{self.height}",
                "type": "2d_fallback"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": type(e).__name__,
                "message": str(e)
            }
    
    def visualize(self, smiles: str, output_base: str, 
                  output_sdf: bool = True,
                  output_image: bool = True,
                  output_html: bool = True,
                  title: Optional[str] = None,
                  input_name: Optional[str] = None) -> Dict[str, Any]:
        """
        可视化分子 3D 结构，生成三种输出
        
        Args:
            smiles: SMILES 字符串
            output_base: 输出文件基础路径（不含扩展名）
            output_sdf: 是否生成 SDF 文件
            output_image: 是否生成 3D 图片
            output_html: 是否生成可交互 HTML
            title: 标题
            input_name: 输入名称（如果有）
        """
        mol = self.smiles_to_mol_3d(smiles)
        
        if mol is None:
            return {
                "smiles": smiles,
                "status": "error",
                "error": "3D generation failed",
                "message": f"无法生成 3D 结构：{smiles}"
            }
        
        is_polymer = self.polymer_handler.is_polymer_smiles(smiles)
        results = {
            "smiles": smiles,
            "status": "success",
            "is_polymer": is_polymer,
            "files": {}
        }
        
        try:
            # 1. 生成 SDF 文件
            if output_sdf:
                sdf_file = f"{output_base}.sdf"
                sdf_result = self.save_sdf(mol, sdf_file)
                if sdf_result["status"] == "success":
                    results["files"]["sdf"] = sdf_file
            
            # 2. 生成 3D 图片
            if output_image:
                img_file = f"{output_base}_3d.png"
                img_result = self.generate_3d_image(mol, img_file, 'png')
                if img_result["status"] == "success":
                    results["files"]["image"] = img_file
            
            # 3. 生成可交互 HTML
            if output_html:
                html_file = f"{output_base}.html"
                html_title = title or ("Polymer 3D Viewer" if is_polymer else "Molecule 3D Viewer")
                html_content = self.generate_html(mol, smiles, html_title, input_name)
                
                html_path = Path(html_file)
                html_path.parent.mkdir(parents=True, exist_ok=True)
                html_path.write_text(html_content, encoding='utf-8')
                results["files"]["html"] = html_file
            
            return results
        except Exception as e:
            return {
                "smiles": smiles,
                "status": "error",
                "error": type(e).__name__,
                "message": str(e)
            }
    
    def visualize_from_name(self, name: str, output_base: str,
                           output_sdf: bool = True,
                           output_image: bool = True,
                           output_html: bool = True) -> Dict[str, Any]:
        """从 IUPAC 名称可视化 3D 结构"""
        smiles = self.name_to_smiles(name)
        
        if smiles is None:
            return {
                "input_name": name,
                "status": "error",
                "error": "Name not found",
                "message": f"OPSIN 无法识别：{name}"
            }
        
        result = self.visualize(
            smiles, output_base,
            output_sdf=output_sdf,
            output_image=output_image,
            output_html=output_html,
            title=name,
            input_name=name
        )
        result["input_name"] = name
        result["smiles"] = smiles
        return result
    
    def visualize_from_file(self, input_file: str, output_base: str,
                           output_sdf: bool = True,
                           output_image: bool = True,
                           output_html: bool = True) -> Dict[str, Any]:
        """从分子文件可视化 3D 结构"""
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                return {
                    "input_file": input_file,
                    "status": "error",
                    "error": "File not found",
                    "message": f"文件不存在：{input_file}"
                }
            
            ext = input_path.suffix.lower()
            
            if ext in ['.sdf', '.sd']:
                suppl = Chem.SDMolSupplier(str(input_path), removeHs=False)
                mol = suppl[0] if len(suppl) > 0 else None
            elif ext == '.mol':
                mol = Chem.MolFromMolFile(str(input_path), removeHs=False)
            elif ext == '.pdb':
                mol = Chem.MolFromPDBFile(str(input_path), removeHs=False)
            else:
                return {
                    "input_file": input_file,
                    "status": "error",
                    "error": "Unsupported format",
                    "message": f"不支持的文件格式：{ext}"
                }
            
            if mol is None:
                return {
                    "input_file": input_file,
                    "status": "error",
                    "error": "Parse error",
                    "message": f"无法解析分子文件：{input_file}"
                }
            
            if mol.GetConformer().Is3D():
                try:
                    if self.force_field.lower() == 'uff':
                        AllChem.UFFOptimizeMolecule(mol, maxIters=self.max_steps)
                    else:
                        AllChem.MMFFOptimizeMolecule(mol, maxIters=self.max_steps)
                except Exception:
                    pass
            else:
                mol = Chem.AddHs(mol)
                params = AllChem.ETKDGv3()
                params.randomSeed = 42
                result = AllChem.EmbedMolecule(mol, params)
                if result == -1:
                    return {
                        "input_file": input_file,
                        "status": "error",
                        "error": "3D generation failed",
                        "message": "无法从 2D 结构生成 3D 坐标"
                    }
                try:
                    if self.force_field.lower() == 'uff':
                        AllChem.UFFOptimizeMolecule(mol, maxIters=self.max_steps)
                    else:
                        AllChem.MMFFOptimizeMolecule(mol, maxIters=self.max_steps)
                except Exception:
                    pass
            
            try:
                smiles = Chem.MolToSmiles(mol)
            except Exception:
                smiles = "unknown"
            
            title = input_path.stem
            result = self.visualize(
                smiles, output_base,
                output_sdf=output_sdf,
                output_image=output_image,
                output_html=output_html,
                title=title,
                input_name=title
            )
            result["input_file"] = input_file
            result["smiles"] = smiles
            return result
        except Exception as e:
            return {
                "input_file": input_file,
                "status": "error",
                "error": type(e).__name__,
                "message": str(e)
            }
    
    def batch_visualize(self, smiles_list: List[str], output_dir: str,
                       output_sdf: bool = True,
                       output_image: bool = True,
                       output_html: bool = True) -> Dict[str, Any]:
        """批量可视化"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        success_count = 0
        
        for i, smiles in enumerate(smiles_list):
            smiles = smiles.strip()
            if not smiles:
                continue
            
            output_base = str(output_path / f"mol_{i+1}")
            result = self.visualize(smiles, output_base, output_sdf, output_image, output_html)
            results.append(result)
            
            if result["status"] == "success":
                success_count += 1
        
        return {
            "status": "completed",
            "total": len(smiles_list),
            "success": success_count,
            "output_dir": str(output_dir),
            "results": results
        }


def main():
    parser = argparse.ArgumentParser(
        description='分子 3D 可视化器（生成 SDF + 3D 图片 + 可交互 HTML）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 生成全部三种输出（SDF + 3D 图片 + HTML）
  %(prog)s --smiles "CCO" --output ethanol
  
  # 只生成 SDF 文件
  %(prog)s --smiles "CCO" --output ethanol --sdf-only
  
  # 只生成 3D 图片
  %(prog)s --smiles "CCO" --output ethanol --image-only
  
  # 只生成 HTML
  %(prog)s --smiles "CCO" --output ethanol --html-only
  
  # 从名称生成
  %(prog)s --name "aspirin" --output aspirin
  
  # 自定义样式
  %(prog)s --smiles "CCO" --output ethanol --style ball_stick
  
  # 批量生成
  %(prog)s --smiles "CCO,C1=CC=CC=C1" --output-dir ./3d_molecules
        '''
    )
    
    parser.add_argument('--smiles', '-s', help='SMILES 字符串（可多个，逗号分隔）')
    parser.add_argument('--name', '-n', help='IUPAC 名称')
    parser.add_argument('--input', '-i', help='输入分子文件（SDF/MOL/PDB）')
    parser.add_argument('--output', '-o', help='输出文件基础路径（不含扩展名）')
    parser.add_argument('--output-dir', '-d',
                        default=str(Path.home() / '.openclaw' / 'media' / 'mol-3d-viewer'),
                        help='输出目录（批量模式）')
    parser.add_argument('--sdf-only', action='store_true',
                        help='只生成 SDF 文件')
    parser.add_argument('--image-only', action='store_true',
                        help='只生成 3D 图片')
    parser.add_argument('--html-only', action='store_true',
                        help='只生成 HTML')
    parser.add_argument('--style', '-S', 
                        choices=['stick', 'sphere', 'ball_stick', 'surface', 'line'],
                        default='ball_stick',
                        help='渲染样式（默认：ball_stick）')
    parser.add_argument('--width', '-W', type=int, default=800,
                        help='图片/网页宽度（默认：800）')
    parser.add_argument('--height', '-H', type=int, default=600,
                        help='图片/网页高度（默认：600）')
    parser.add_argument('--bg-color', '-b', default='white',
                        help='背景颜色（默认：white）')
    parser.add_argument('--show-labels', '-l', action='store_true', default=True,
                        help='显示原子标签（默认：开启）')
    parser.add_argument('--hide-labels', action='store_false', dest='show_labels',
                        help='隐藏原子标签')
    parser.add_argument('--auto-rotate', '-r', action='store_true',
                        help='HTML 自动旋转')
    parser.add_argument('--force-field', choices=['mmff94', 'uff'], default='mmff94',
                        help='力场类型（默认：mmff94）')
    parser.add_argument('--max-steps', type=int, default=200,
                        help='力场优化最大步数（默认：200）')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='安静模式，只输出结果')
    
    args = parser.parse_args()
    
    viewer = Mol3DViewer(
        width=args.width,
        height=args.height,
        style=args.style,
        bg_color=args.bg_color,
        show_labels=args.show_labels,
        auto_rotate=args.auto_rotate,
        force_field=args.force_field,
        max_steps=args.max_steps
    )
    
    # 确定输出类型
    if args.sdf_only:
        output_sdf, output_image, output_html = True, False, False
    elif args.image_only:
        output_sdf, output_image, output_html = False, True, False
    elif args.html_only:
        output_sdf, output_image, output_html = False, False, True
    else:
        output_sdf, output_image, output_html = True, True, True
    
    try:
        results = None
        
        if args.input:
            if not args.output:
                input_name = Path(args.input).stem
                args.output = f"{input_name}_3d"
            result = viewer.visualize_from_file(
                args.input, args.output,
                output_sdf=output_sdf,
                output_image=output_image,
                output_html=output_html
            )
            results = {"status": "success", "results": [result]}
        
        elif args.smiles:
            smiles_list = [s.strip() for s in args.smiles.split(',')]
            
            if len(smiles_list) > 1:
                results = viewer.batch_visualize(
                    smiles_list, args.output_dir,
                    output_sdf=output_sdf,
                    output_image=output_image,
                    output_html=output_html
                )
            else:
                if not args.output:
                    args.output = "mol_3d"
                result = viewer.visualize(
                    smiles_list[0], args.output,
                    output_sdf=output_sdf,
                    output_image=output_image,
                    output_html=output_html
                )
                results = {"status": "success", "results": [result]}
        
        elif args.name:
            if not args.output:
                safe_name = "".join(c for c in args.name if c.isalnum() or c in '-_').strip()
                args.output = f"{safe_name}_3d"
            result = viewer.visualize_from_name(
                args.name, args.output,
                output_sdf=output_sdf,
                output_image=output_image,
                output_html=output_html
            )
            results = {"status": "success", "results": [result]}
        
        else:
            parser.error("必须指定 --smiles、--name 或 --input")
        
        if not args.quiet:
            if results.get("results"):
                for r in results["results"]:
                    if r.get("status") == "success":
                        polymer_tag = " [聚合物]" if r.get("is_polymer") else ""
                        print(f"✓ 已生成 3D 优化结构{polymer_tag}")
                        
                        files = r.get("files", {})
                        if files.get("sdf"):
                            print(f"  📄 SDF: {files['sdf']}")
                        if files.get("image"):
                            print(f"  🖼️  3D 图片：{files['image']}")
                        if files.get("html"):
                            print(f"  🌐 HTML: {files['html']} (可交互，支持旋转)")
                    else:
                        print(f"✗ 失败：{r.get('input_name', r.get('smiles', r.get('input_file', 'Unknown')))} - {r.get('message', 'Unknown error')}")
                
                if results.get("total"):
                    print(f"\n完成：{results['success']}/{results['total']} 成功")
            else:
                print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
