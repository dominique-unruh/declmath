package declmath

import scala.collection.mutable

/**
  * Created by unruh on 5/21/17.
  */
class TypeCheck {
}

case class Sort(classes : List[String])

sealed trait Type {
  def subst(sub: Map[TVar, Type]): Type
}

object Type {
  def fun(args:Type*) = TCon("fun",args.toList)
  val real = TCon("real",Nil)
}

final case class TVar(name:String) extends Type{
  override def toString : String = name
  override def subst(sub: Map[TVar, Type]): Type = sub.get(this) match {
    case None => this
    case Some(t) => t
  }
}
final case class TCon(name:String, args:List[Type]) extends Type {
  override def toString : String = if (args.isEmpty) name else name + "(" + args.mkString(",") + ")"
  override def subst(sub: Map[TVar, Type]): Type = TCon(name,args.map(_.subst(sub)))
}

sealed trait Constraint {
  def subst(sub: Map[TVar, Type]): Constraint

  def process(env: TypeEnvM) : Seq[Constraint] = this match {
    case AppConstraint(appType,headType,argTypes) =>
      List(EqConstraint(headType,Type.fun(argTypes ++ List(appType) : _*)))
    case EqConstraint(TCon(name1,args1),TCon(name2,args2)) =>
      assert(name1==name2)
      assert(args1.length==args2.length)
      args1.zip(args2).map { case (x,y) => EqConstraint(x,y) }
    case EqConstraint(tv : TVar,t) =>
      env.lookup(tv) match {
        case Some(u) => List(EqConstraint(t,u))
        case None => env.instantiate(tv,t); Nil
      }
    case EqConstraint(t,tv:TVar) => EqConstraint(tv,t).process(env)
  }
}

final case class AppConstraint(appType:Type, headType:Type, argTypes:List[Type]) extends Constraint {
  override def subst(sub: Map[TVar, Type]): AppConstraint = AppConstraint(appType.subst(sub),headType.subst(sub),argTypes.map(_.subst(sub)))
}
final case class EqConstraint(a:Type, b:Type) extends Constraint {
  override def subst(sub: Map[TVar, Type]): EqConstraint = EqConstraint(a.subst(sub),b.subst(sub))
}
final case class SortConstraint(typ:Type, sort:Sort) extends Constraint {
  override def subst(sub: Map[TVar, Type]): SortConstraint = SortConstraint(typ.subst(sub),sort)
}

/** Not thread safe */
class TypeConstraintsM {
  val constraints = new mutable.Queue[Constraint]
  def add(cons:Constraint) : Unit = constraints.enqueue(cons)
  def add(appType: Type, headType: Type, argTypes : Type*) : Unit =
    constraints.enqueue(AppConstraint(appType,headType,argTypes.toList))
  def toTypeCostraints: TypeConstraints = TypeConstraints.fromTypeConstraintsM(this)
  def toList: List[Constraint] = constraints.toList

  def inference(env:TypeEnvM): Unit = {
    while (constraints.nonEmpty) {
      val constraint = constraints.dequeue()
      println("Processing "+constraint)
      val results = constraint.process(env)
      println("New constraints: "+results)
      constraints.enqueue(results:_*)
    }
  }
}

class TypeConstraints private (private val constraints : List[Constraint]) {
  override def toString: String = constraints.toString
}
object TypeConstraints {
  def fromTypeConstraintsM(constraints:TypeConstraintsM) = new TypeConstraints(constraints.toList)
}

class TypeEnv private (private val types : Map[String,Option[Type]]) {
  override def toString: String = types.toString
}
object TypeEnv {
  def fromTypeEnvM(env:TypeEnvM) = new TypeEnv(env.toMap)
}

/** Not thread safe */
class TypeEnvM {
  private val types : mutable.Map[String,Option[Type]] = new mutable.HashMap()
  private var counter : Int = 0

  def toMap : Map[String,Option[Type]] = {
    for (tv <- types.keys) lookup(TVar(tv))
    types.toMap
  }
  def toTypeEnv : TypeEnv = TypeEnv.fromTypeEnvM(this)

  def lookup(tvar:TVar) : Option[Type] = types(tvar.name) match {
    case None => None
    case Some(repl) =>
      val repl2 = get(repl)
      if (repl != repl2) types.update(tvar.name,Some(repl2))
      Some(repl2)
  }
  def get(typ:Type) : Type = typ match {
    case tv:TVar => lookup(tv) match {
      case None => tv
      case Some(repl) => repl
    }
    case TCon(name,args) => TCon(name,args.map(this.get))
  }
  def instantiate(tvar:TVar, typ:Type) : Unit = {
    assert(types.get(tvar.name).contains(None)) // Must be declared but uninitialized
    types.update(tvar.name,Some(typ))
  }
  def newTVar(pfx:String) : TVar = {
    var name = pfx
    while (types.contains(name)) { name = pfx+counter; counter += 1 }
    types.update(name,None)
    TVar(name)
  }
  def newTVars(typ: Type): (Type,Map[TVar,Type]) = {
    val tvs = new mutable.HashMap[TVar,TVar]
    def f(typ:Type) : Type = typ match {
      case tv:TVar => tvs.getOrElseUpdate(tv,newTVar(tv.name))
      case TCon(con,args) => TCon(con,args.map(f))
    }
    val typ2 = f(typ)
    (typ2,tvs.toMap)
  }
}


