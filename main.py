from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response, Path
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session, joinedload
from models import Enduro, Competitor, Checkpoint, Tempo, Category

from datetime import datetime, timedelta
from fastapi import Body

from time import time
from database import get_db, SessionLocal, engine

from configs import adicionar_coluna_tempo
from calculos import contar_registros

# Configuração do Jinja2Templates
templates = Jinja2Templates(directory="templates")

app = FastAPI()


        
def seconds_to_hms(seconds: float) -> str:
    """Converte segundos para o formato HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def hms_to_seconds(hours: int, minutes: int, seconds: int) -> float:
    """Converte horas, minutos e segundos para segundos."""
    return hours * 3600 + minutes * 60 + seconds

# Funções para mensagens flash
def set_flash_message(response: Response, message: str, category: str = "success"):
    response.set_cookie(key="flash_message", value=message)
    response.set_cookie(key="flash_category", value=category)

def get_flash_message(request: Request):
    flash_message = request.cookies.get("flash_message")
    flash_category = request.cookies.get("flash_category")
    return flash_message, flash_category

# Middleware para limpar mensagens flash após exibi-las
@app.middleware("http")
async def clear_flash_messages(request: Request, call_next):
    response = await call_next(request)
    
    if request.cookies.get("flash_message"):
        response.delete_cookie("flash_message")
        response.delete_cookie("flash_category")
    
    return response

# Página inicial
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Rotas para Enduros
@app.get("/enduros/create/", response_class=HTMLResponse)
def create_enduro_form(request: Request):
    return templates.TemplateResponse("create_enduro.html", {"request": request, "enduro": Enduro})

#Rota para inserir um enduro
@app.post("/enduros/", response_class=RedirectResponse)
def create_enduro(
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    date: str = Form(...),
    hora_largada: str = Form(...),
    db: Session = Depends(get_db),
    response: Response = Response
):
    
    hora_largada_obj = datetime.strptime(hora_largada, "%H:%M").time()

    db_enduro = Enduro(name=name, location=location, date=date, hora_largada=hora_largada)
    db.add(db_enduro)
    db.commit()
    db.refresh(db_enduro)
    
    set_flash_message(response, "Enduro criado com sucesso!", "success")
    return RedirectResponse(url=f"/enduros/{db_enduro.id}/", status_code=303)

#Rota para visualizar enduros 
@app.get("/enduros/", response_class=HTMLResponse)
def list_enduros(request: Request, db: Session = Depends(get_db)):
    enduros = db.query(Enduro).all()
    return templates.TemplateResponse("list_enduros.html", {"request": request, "enduros": enduros})

@app.get("/enduros/{enduro_id}/", response_class=HTMLResponse)
def enduro_detail(enduro_id: int, request: Request, db: Session = Depends(get_db)):
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    return templates.TemplateResponse("enduro_detail.html", {"request": request, "enduro": enduro})

# Rota para editar os enduros

@app.get("/enduros/{enduro_id}/edit/", response_class=HTMLResponse)
def edit_enduro_form(enduro_id: int, request: Request, db: Session = Depends(get_db)):
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    return templates.TemplateResponse("edit_enduro.html", {"request": request, "enduro": enduro})

#Rota para editar os enduros
@app.post("/enduros/{enduro_id}/update/", response_class=RedirectResponse)
def update_enduro(
    enduro_id: int,
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    date: str = Form(...),
    hora_largada: str = Form(...),
    db: Session = Depends(get_db),
    response: Response = Response
):
    db_enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not db_enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    
    db_enduro.name = name
    db_enduro.location = location
    db_enduro.date = date
    db_enduro.hora_largada = hora_largada
   
    db.commit()
    db.refresh(db_enduro)
    
    set_flash_message(response, "Enduro atualizado com sucesso!", "success")
    return RedirectResponse(url="/enduros/", status_code=303)

# Rota para deletar os enduros

@app.post("/enduros/{enduro_id}/delete/", response_class=RedirectResponse)
def delete_enduro(
    enduro_id: int,
    db: Session = Depends(get_db),
    response: Response = Response
):
    db_enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not db_enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    
    
    db.delete(db_enduro)
    db.commit()    
   

    
    set_flash_message(response, "Enduro excluído com sucesso!", "success")
    return RedirectResponse(url="/enduros/", status_code=303)

# Rotas para ver adicionar Competidores
@app.get("/enduros/{enduro_id}/competitors/create", response_class=HTMLResponse)
def create_competitor_form(request: Request, enduro_id: int, db: Session = Depends(get_db)):
    
    categories = db.query(Category).all()  # Buscar todas as categorias do banco
    db_enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not db_enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    return templates.TemplateResponse("create_competitor.html", 
                                      {"request": request, "enduro": enduro_id, "categories": categories})


#rota para adicionar competidores
@app.post("/enduros/{enduro_id}/competitors/", response_class=RedirectResponse)
def create_competitor(
    enduro_id: int,
    request: Request,
    name: str = Form(...),
    placa: str = Form(...),
    categories_id: int = Form(...),
    db: Session = Depends(get_db),
    response: Response = Response
):
    db_competitor = Competitor(name=name, enduro_id = enduro_id, placa=placa, categories_id = categories_id)
    db.add(db_competitor)
    db.commit()
    db.refresh(db_competitor)
    
    
    
    set_flash_message(response, "Competidor adicionado com sucesso!", "success")
    return RedirectResponse(url=f"/enduros/", status_code=303)

# Rota para editar os competidores

@app.get("/enduros/{enduro_id}/competitors/{competitor_id}/edit/", response_class=HTMLResponse)
def edit_competitor_form(enduro_id: int, competitor_id: int, request: Request, db: Session = Depends(get_db)):
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    categories = db.query(Category).all()  # Buscar todas as categorias do banco
    if not competitor:
        raise HTTPException(status_code=404, detail="Competidor não encontrado")
    return templates.TemplateResponse("edit_competitor.html", {"request": request, "competitor": competitor, "categories": categories})

@app.post("/enduros/{enduro_id}/competitors/{competitor_id}/update/", response_class=RedirectResponse)
def update_competitor(
    enduro_id: int,
    competitor_id: int, 
    request: Request,
    name: str = Form(...),
    placa: str = Form(...),
    categories_name: str = Form(...),
    db: Session = Depends(get_db),
):
    db_competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not db_competitor:
        raise HTTPException(status_code=404, detail="Competidor não encontrado")
    
    try:
        db_competitor.name = name
        db_competitor.placa = placa
        db_competitor.categories_name = categories_name
       
        db.commit()
        db.refresh(db_competitor)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao atualizar o competidor")
    
    # Supondo que você tenha uma função set_flash_message para definir mensagens flash
    set_flash_message(request, "Competidor atualizado com sucesso!", "success")
    
    # Redireciona para a página de detalhes do enduro ou para a lista de competidores
    return RedirectResponse(url=f"/enduros/", status_code=303)

# Rota para deletar os enduros

@app.post("/enduros/{enduro_id}/delete/", response_class=RedirectResponse)
def delete_enduro(
    enduro_id: int,
    db: Session = Depends(get_db),
    response: Response = Response
):
    db_enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not db_enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    
    
    db.delete(db_enduro)
    db.commit()    
   

    
    set_flash_message(response, "Enduro excluído com sucesso!", "success")
    return RedirectResponse(url="/enduros/", status_code=303)

# rota para ver lista de competidores 

@app.get("/enduros/{enduro_id}/competitors/", response_class=HTMLResponse) 
def list_competitors(enduro_id: int, request: Request, db: Session = Depends(get_db)):
    
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    
    competitors = db.query(Competitor).options(joinedload(Competitor.category)).filter(Competitor.enduro_id == enduro_id).all()
    return templates.TemplateResponse("list_competitors.html", {"request": request, "enduro": enduro, "competitors": competitors})# Rotas para Checkpoints

#Criando Checkpoint 
@app.get("/enduros/{enduro_id}/checkpoints/create/", response_class=HTMLResponse)
def create_checkpoint_form(enduro_id: int, request: Request, db: Session = Depends(get_db)):
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    return templates.TemplateResponse("create_checkpoint.html", {"request": request, "enduro": enduro})

@app.post("/enduros/{enduro_id}/checkpoints/", response_class=RedirectResponse)
def create_checkpoint(
    enduro_id: int,
    request: Request,
    checkpoint_name: str = Form(...),
    tempo: float = Form(...),  # Este campo agora deve receber um float do formulário
    db: Session = Depends(get_db),
    response: Response = Response
):

    try:
        # Verifica se o enduro existe
        enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
        if not enduro:
            raise HTTPException(status_code=404, detail="Enduro não encontrado")

        # Cria o checkpoint
        db_checkpoint = Checkpoint(checkpoint_name=checkpoint_name, time=tempo, enduro_id=enduro_id)
        db.add(db_checkpoint)
        db.commit()
        db.refresh(db_checkpoint)

        # Adiciona uma nova coluna para o tempo do checkpoint, se necessário
        adicionar_coluna_tempo(checkpoint_name)

        # Define uma mensagem de sucesso
        set_flash_message(response, "Checkpoint adicionado com sucesso!", "success")
        return RedirectResponse(url=f"/enduros/{enduro_id}/", status_code=303)
    except Exception as e:
        # Em caso de erro, faz rollback e levanta uma exceção
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar checkpoint: {str(e)}")
# Rota Lista checkpoints

#Rota para visualizar checkpoints 
@app.get("/enduros/{enduro_id}/checkpoints/", response_class=HTMLResponse)
def list_checkpoints(request: Request, enduro_id: int, db: Session = Depends(get_db)):
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    
    
    
    checkpoints = db.query(Checkpoint).filter(Checkpoint.enduro_id == enduro_id).all()
    
     # Formatando o tempo de cada checkpoint
    for checkpoint in checkpoints:
        # Convertendo o tempo (float) para timedelta
        formatted_time = str(timedelta(seconds=checkpoint.time))
        
        # Ajustar o formato para garantir HH:MM:SS, mesmo para tempos abaixo de uma hora
        hours, remainder = divmod(checkpoint.time, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Criar o formato desejado
        formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        checkpoint.formatted_time = formatted_time

    
    
    return templates.TemplateResponse("list_checkpoints.html", {"request": request, "checkpoints": checkpoints, "enduro": enduro})



#Rota para lançamento dos tempos

@app.get("/enduros/{enduro_id}/checkpoints/{checkpoint_id}/competitors/", response_class=HTMLResponse)
def list_competitors_for_checkpoint(enduro_id: int, checkpoint_id: int, request: Request, db: Session = Depends(get_db)):
    
    # Busca o checkpoint no banco de dados
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    
    checkpoint = db.query(Checkpoint).filter(Checkpoint.id == checkpoint_id).first()
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint não encontrado")
    
    # Busca os competidores associados ao enduro do checkpoint
    competitors = db.query(Competitor).filter(Competitor.enduro_id == checkpoint.enduro_id).all()
    
    
    
    return templates.TemplateResponse("list_competitors_for_checkpoint.html", {
        "request": request,
        "enduro": enduro,
        "competitor": competitors,
        "checkpoints": checkpoint,
        "competitors": [{"hora_largada": competitor.hora_largada.strftime("%H:%M")} for competitor in competitors]
    })
    
   

@app.post("/enduros/{enduro_id}/checkpoints/{checkpoint_id}/competitors/{competitor_id}/update/")
def update_tempos(
    enduro_id: int,
    request: Request,
    competitor_id: int,
    checkpoint_id: int,
    hora_largdada: str,
    checkpoint_name: str, 
    db: Session = Depends(get_db),
    response: Response = Response
):
    # Recuperar o enduro para pegar o horário de largada
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()

    if not enduro:
        set_flash_message(response, "Enduro não encontrado.", "error")
        return RedirectResponse(url=f"/enduros/", status_code=303)

    # Converter a hora de largada do enduro em datetime e adicionar 1 minuto
    hora_largada_enduro = datetime.combine(datetime.today(), enduro.hora_largada)
    hora_largada_competidor = hora_largada_enduro + timedelta(minutes=1)

    # Criar o competidor com a hora de largada calculada
    db_tempo = Tempo(
        enduro_id= enduro_id,
        competitor_id=competitor_id,
        checkpoint_id=checkpoint_id,
        hora_largada=hora_largada_competidor,
        checkpoint_name=checkpoint_name
        
    )
    
    db.add(db_tempo)
    db.commit()
    db.refresh(db_tempo)
    
    set_flash_message(response, "Competidor adicionado com sucesso!", "success")
    return RedirectResponse(url=f"/enduros/", status_code=303)





#Rota para inserir um categorias

@app.get("/enduros/{enduro_id}/category/create", response_class=HTMLResponse)
def create_category_form(enduro_id: int,  request: Request, db: Session = Depends(get_db)):
    
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")
    
    return templates.TemplateResponse("create_category.html", {"request": request, "enduro": enduro})

@app.post("/enduro/{enduro_id}/category", response_class=RedirectResponse)
def create_category(
    request: Request,
    enduro_id: int,
    name: str = Form(...),
    db: Session = Depends(get_db),
    response: Response = Response
):
    db_category = Category( enduro_id=enduro_id, name=name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    set_flash_message(response, "Categoria criada com sucesso!", "success")
    return RedirectResponse(url=f"/enduros/", status_code=303)

#Rota para visualizar categorias 
@app.get("/enduros/{enduro_id}/categories/", response_class=HTMLResponse)
def list_category(request: Request, enduro_id: int, db: Session = Depends(get_db)):
    categories = db.query(Category).all()  # Corrigido para pegar todas as categorias
    return templates.TemplateResponse("list_categories.html", {"request": request, "categories": categories, "enduro_id": enduro_id})

# Rota para editar os categorias

@app.get("/enduros/{enduro_id}/categories/{category_id}/edit/", response_class=HTMLResponse)
def edit_category_form(
    enduro_id: int,
    category_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    # Verifica se o enduro existe
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")

    # Verifica se a categoria existe
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    return templates.TemplateResponse(
        "edit_category.html",
        {"request": request, "enduro": enduro, "category": category}
    )
    x
@app.post("/enduros/{enduro_id}/categories/{category_id}/update/", response_class=RedirectResponse)
def update_category(
    enduro_id: int,
    category_id: int,
    category_name: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verifica se o enduro existe
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")

    # Verifica se a categoria existe
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    # Atualiza o nome da categoria
    db_category.name = category_name  # Certifique-se de que o campo no modelo se chama `name`
    db.commit()
    db.refresh(db_category)

    # Redireciona para a página do enduro ou da categoria
    return RedirectResponse(url=f"/enduros/{enduro_id}/categories/", status_code=303)
# Rota para deletar os categorias

@app.post("/enduros/{enduro_id}/categories/{category_id}/delete/", response_class=RedirectResponse)
def delete_category(
    enduro_id: int,
    category_id: int, 
    db: Session = Depends(get_db),
    response: Response = Response
):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    
    db.delete(db_category)
    db.commit()    
 
@app.get("/enduros/{enduro_id}/listalargada/", response_class=HTMLResponse)
def list_largada(enduro_id: int, request: Request, db: Session = Depends(get_db)):
    # Busca o enduro no banco de dados
    enduro = db.query(Enduro).filter(Enduro.id == enduro_id).first()
    if not enduro:
        raise HTTPException(status_code=404, detail="Enduro não encontrado")

    # Busca os competidores associados ao enduro
    competitors = db.query(Competitor).filter(Competitor.enduro_id == enduro_id).all()

    # Calcula a hora de largada para cada competidor
    largada_list = []
    hora_largada_base = datetime.strptime(enduro.hora_largada, "%H:%M")  # Converte a hora de largada base para um objeto datetime

    for i, competitor in enumerate(competitors):
        # Adiciona i minutos à hora de largada base
        hora_largada_competitor = (hora_largada_base + timedelta(minutes=i)).strftime("%H:%M")
        
        # Busca o nome da categoria do competidor
        category = db.query(Category).filter(Category.id == competitor.categories_id).first()
        category_name = category.name if category else "Sem categoria"

        # Adiciona o competidor à lista de largada
        largada_list.append({
            "name": competitor.name,
            "category": category_name,
            "hora_largada": hora_largada_competitor
        })

    return templates.TemplateResponse(
        "list_largada.html",
        {"request": request, "enduro": enduro, "largada_list": largada_list}
    )
    
    


# Executar o aplicativo
if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level='info' , reload=True )