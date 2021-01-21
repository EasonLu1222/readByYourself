# Generate/update the translation file and save them under ./translate folder
pylupdate5 $(ls ./ui/*.py|tr '\n' ' ') app.py  -ts ./translate/en_US.ts
pylupdate5 $(ls ./ui/*.py|tr '\n' ' ') app.py  -ts ./translate/zh_TW.ts
pylupdate5 $(ls ./ui/*.py|tr '\n' ' ') app.py  -ts ./translate/zh_CN.ts
pylupdate5 $(ls ./ui/*.py|tr '\n' ' ') app.py  -ts ./translate/vi.ts