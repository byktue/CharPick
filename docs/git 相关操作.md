推送到后端分支
```bash
git push origin main:backend
```

建立远程连接
```bash
git branch --set-upstream-to=origin/backend main
```

检查是否成功
```bash
git branch -vv
```

将当前分支改名为backend然后重新关联
```bash
# 将当前分支（main）改名为 backend 
git branch -m backend 
# 然后重新关联 
git push -u origin backend
```

