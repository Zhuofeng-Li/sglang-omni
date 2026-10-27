from pathlib import Path
import ast, hashlib, json, os, types
path=Path('/opt/sglang/lib/python3.12/site-packages/flashinfer/compilation_context.py')
source=path.read_text()
tree=ast.parse(source)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CompilationContext')
class MockCuda:
 def device_count(self): return 1
 def get_device_capability(self, device): return (9,0)
ns={'os':types.SimpleNamespace(environ={}), 'torch':types.SimpleNamespace(cuda=MockCuda()), 'logger':types.SimpleNamespace(warning=lambda *args:None)}
exec(compile(ast.Module(body=[cls],type_ignores=[]),str(path),'exec'),ns)
a=sorted(ns['CompilationContext']().TARGET_CUDA_ARCHS)
ns['os'].environ={'FLASHINFER_CUDA_ARCH_LIST':'9.0a'}
b=sorted(ns['CompilationContext']().TARGET_CUDA_ARCHS)
assert a==b==[(9,'0a')]
print(json.dumps({'source_path':str(path),'sha256':hashlib.sha256(source.encode()).hexdigest(),'visible_capability':[9,0],'automatic_targets':a,'explicit_9_0a_targets':b,'equal':a==b,'method':'Execute exact installed CompilationContext AST with mocked capability; no Torch import, CUDA allocation or JIT.'}))
