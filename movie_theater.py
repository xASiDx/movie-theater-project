import config #contains DB config and secret key
from flask import Flask, render_template, request, session
from DBcm import UseDatabase, ConnectionError, CredentialsError, SQLError
from functools import wraps

app = Flask(__name__)
app.secret_key = config.secret_key
app.config["dbconfig"] = config.dbconfig

@app.route("/")
def entry_page() -> "html":
    title = "Добро пожаловать в кинотеатр \"У Сергеичей\"!"
    return render_template("index.html", page_title=title)

@app.route("/movies", methods=["GET", "POST"])
def movies_mgmt() -> "html":
    #Delete requests only contain movie id values as dictionary keys,
    #so if there are no other keys, then it is a delete request
    if request.method == "POST":
        try:
            if "rel_year" not in request.form.keys():
                #print("Deleting movies")
                db_del_movie(request)
            elif "id" in request.form.keys():
                #print("Editing a movie")
                db_edit_movie(request)
            else:
                #print("Adding a movie")
                db_add_movie(request)
        except ConnectionError as err:
            print("Database connection error:", str(err))
        except CredentialsError as err:
            print("Database authentication error:", str(err))
        except SQLError as err:
            print("Something is worng with the SQL request:", str(err))
        except Exception as err:
            print("Error:", str(err))
    _SQL = """select id, rel_year, title_ru, title_orig, duration,
              descr, genre, age_restr, director, cast
              from movies
              order by rel_year, title_ru, title_orig"""
    try:
        contents = db_request(_SQL)
        title = "Список доступных фильмов"
        col_titles = ("Год", "Название", "Оригинальное название",
                      "Продолжит. (мин)", "Описание", "Жанр", 
                      "Возрастное огранич.", "Режиссёр", "В ролях")
        return render_template("db_mgmt.html",
                               page_title=title,
                               action1="/movies_add",
                               action2="/movies_edit",
                               action3="/movies_delete",
                               col_titles=col_titles,
                               data=contents)
    except ConnectionError as err:
        print("Database connection error:", str(err))
    except CredentialsError as err:
        print("Database authentication error:", str(err))
    except SQLError as err:
        print("Something is worng with the SQL request:", str(err))
    except Exception as err:
        print("Error:", str(err))
    return "Error"

@app.route("/movies_add", methods=["GET", "POST"])
def add_movie() -> "html":
    title = "Добавить новый фильм"
    return render_template("movies_add.html", 
                           page_title=title, 
                           action1="/movies")

def db_add_movie(req: "flask_request") -> None:
    """Add information about a movie to the database"""
    with UseDatabase(app.config["dbconfig"]) as cursor:
        _SQL = """insert into movies
                  (title_ru, title_orig, rel_year, duration,
                  descr, genre, age_restr, director, cast)
                  values
                  (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(_SQL, (req.form["title_ru"], 
                              req.form["title_orig"],
                              req.form["rel_year"],
                              req.form["duration"],
                              req.form["descr"],
                              req.form["genre"],
                              req.form["age_restr"],
                              req.form["director"],
                              req.form["cast"]))

@app.route("/movies_edit", methods=["POST"])
def edit_movie() -> "html":
    #Taking only first id received from the form
    movie_id = list(request.form.keys())[list(request.form.values()).index("id")]
    _SQL = """select * from movies
              where id = %s"""
    try:
        contents = db_request(_SQL, movie_id)
        title = "Редактирование фильмов"
        return render_template("edit.html", 
                               page_title=title,
                               data=contents,
                               action1="/movies")
    except ConnectionError as err:
        print("Database connection error:", str(err))
    except CredentialsError as err:
        print("Database authentication error:", str(err))
    except SQLError as err:
        print("Something is worng with the SQL request:", str(err))
    except Exception as err:
        print("Error:", str(err))
    return "Error"

def db_edit_movie(req: "flask_request") -> None:
    with UseDatabase(app.config["dbconfig"]) as cursor:
        _SQL = """update movies
                  set title_ru = %s, title_orig = %s, rel_year = %s,
                  duration = %s, descr = %s, genre = %s, age_restr = %s,
                  director = %s, cast = %s
                  where id = %s"""
        cursor.execute(_SQL, (req.form["title_ru"], 
                              req.form["title_orig"],
                              req.form["rel_year"],
                              req.form["duration"],
                              req.form["descr"],
                              req.form["genre"],
                              req.form["age_restr"],
                              req.form["director"],
                              req.form["cast"],
                              req.form["id"]))

def add_id(_SQL: str, req: "flask_request") -> str:
    req_keys = list(req.form.keys())
    param_list = []
    for i in range(len(req_keys)):
        param_list.append("""id = %s""")
    _SQL += """ or """.join(param_list)
    return _SQL, req_keys

@app.route("/movies_delete", methods=["POST"])
def delete_movie() -> "html":
    _SQL = """select id, title_ru, title_orig, rel_year, director
              from movies
              where """
    _SQL, req_keys = add_id(_SQL, request)
    _SQL += """ order by rel_year"""
    try:
        contents = db_request(_SQL, *req_keys)
        title = "Удаление фильмов"
        return render_template("delete.html", 
                               page_title=title,
                               obj="фильмы",
                               action1="/movies",
                               data=contents)
    except ConnectionError as err:
        print("Database connection error:", str(err))
    except CredentialsError as err:
        print("Database authentication error:", str(err))
    except SQLError as err:
        print("Something is worng with the SQL request:", str(err))
    except Exception as err:
        print("Error:", str(err))
    return "Error"

def db_del_movie(req: "flask_request") -> None:
    with UseDatabase(app.config["dbconfig"]) as cursor:
        _SQL = """delete from movies
                  where """
        _SQL, req_keys = add_id(_SQL, request)
        cursor.execute(_SQL, req_keys)

@app.route("/cinema_halls", methods=["GET", "POST"])
def cin_halls_mgmt() -> "html":
    if request.method == "POST":
        if "name" not in request.form.keys():
            db_del_cin_hall(request)
        else:
            db_add_cin_hall(request)
    _SQL = """select * from cin_halls;"""
    try:
        contents = db_request(_SQL)
        title = "Кинозалы"
        col_titles = ("Название", "Расположение")
        return render_template("db_mgmt.html",
                               page_title=title,
                               action1="/cinema_halls_add",
                               action2="/cinema_halls_edit",
                               action3="/cinema_halls_delete", 
                               col_titles=col_titles,
                               data=contents)
    except ConnectionError as err:
        print("Database connection error:", str(err))
    except CredentialsError as err:
        print("Database authentication error:", str(err))
    except SQLError as err:
        print("Something is worng with the SQL request:", str(err))
    except Exception as err:
        print("Error:", str(err))
    return "Error"

@app.route("/cinema_halls_add", methods=["GET", "POST"])
def add_cin_hall() -> "html":
    return render_template("cin_halls_add.html", 
                           page_title="Добавить кинозал",
                           action1="/cinema_halls")

def db_add_cin_hall(req: "flask_request") -> None:
    with UseDatabase(app.config["dbconfig"]) as cursor: 
        _SQL = """insert into cin_halls
                  (name, location)
                  values
                  (%s, %s)"""
        cursor.execute(_SQL, (req.form["name"], req.form["location"]))
    _SQL = """select max(id) as max_id from cin_halls"""
    cin_hall_id = db_request(_SQL)[0][0]
    #This seems not safe
    new_table_name = "cin_hall_" + str(cin_hall_id)
    #For now I'm assuming that rows contain equal numbers of seats
    seats = []
    for i in range(int(req.form["row_num"])):
        for j in range (int(req.form["seats_in_row"])):
            seats.append(f"({i + 1}, {j + 1})")
    #There shold be a more safe and elegant way to do this
    with UseDatabase(app.config["dbconfig"]) as cursor: 
        _SQL = f"""create table {new_table_name} (
                   id int primary key auto_increment,
                   row_num tinyint,
                   seat tinyint
                   );
                   insert into {new_table_name}
                   (row_num, seat)
                   values """ + ", ".join(seats)
        for result in cursor.execute(_SQL, multi=True):
            print("\n", cursor.statement, "\n")

@app.route("/cinema_halls_edit", methods=["POST"])
def edit_cin_hall() -> "html":
    return render_template("index.html", page_title="Edit the cinema hall")

@app.route("/cinema_halls_delete", methods=["POST"])
def del_cin_hall() -> "html":
    _SQL = """select *
              from cin_halls
              where """
    _SQL, req_keys = add_id(_SQL, request)
    _SQL += """ order by name"""
    try:
        contents = db_request(_SQL, *req_keys)
        title = "Удаление кинозалов"
        return render_template("delete.html", 
                               page_title=title,
                               obj="кинозалы",
                               action1="/cinema_halls",
                               data=contents)
    except ConnectionError as err:
        print("Database connection error:", str(err))
    except CredentialsError as err:
        print("Database authentication error:", str(err))
    except SQLError as err:
        print("Something is worng with the SQL request:", str(err))
    except Exception as err:
        print("Error:", str(err))
    return "Error"

def db_del_cin_hall(req: "flask_request") -> None:
    with UseDatabase(app.config["dbconfig"]) as cursor:
        _SQL = """delete from cin_halls
                  where """
        _SQL, req_keys = add_id(_SQL, request)
        cursor.execute(_SQL, req_keys)
        #There shold be a more safe and elegant way to do this
        _SQL = """"""
        for c_h_id in req_keys:
            _SQL += f"""drop table cin_hall_{c_h_id};"""
        for result in cursor.execute(_SQL, multi=True):
            pass
        

def db_request(_SQL: str, *args) -> list:
    with UseDatabase(app.config["dbconfig"]) as cursor:
        cursor.execute(_SQL, (args))
        data = cursor.fetchall()
        #print(cursor.statement)
    return data

if __name__ == "__main__":
    app.run(debug=True)