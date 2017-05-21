package declmath

import scala.collection.mutable
import scala.xml.{Elem, Node}

/**
  * Created by unruh on 5/21/17.
  */


case class Info(id:Option[String], presentation:Option[String])

sealed abstract case class CMathML(info:Info) {
  def getTypeConstraints(consts:Map[(String,String),(Type,Seq[Constraint])]) : (TypeEnvM,TypeConstraintsM,Type,Map[String,Type]) = {
    var env = new TypeEnvM
    var constraints = new TypeConstraintsM
    var varTypes = new mutable.HashMap[String,TVar]()

    def collect(m:CMathML) : Type = m match {
      case CI(name) => varTypes.getOrElseUpdate(name, env.newTVar(name))
      case CSymbol(cd,name) =>
        val (typ,cons) = consts((cd, name))
        val (typ2, tvs) = env.newTVars(typ)
        for (c <- cons) constraints.add(c.subst(tvs))
        typ2
      case CApply(head,args@_*) =>
        val headType = collect(head)
        val argTypes = args.map(collect)
        val appVar = env.newTVar("app")
        constraints.add(appVar,headType,argTypes:_*)
        appVar
    }

    val self = collect(this)
    (env,constraints,self,varTypes.toMap)
  }
}
object CMathML {
  def fromPMML(xml:scala.xml.Node) : CMathML = xml match {
    case Elem(_,"math",_,_,Elem(_,"semantics",_,_,_,anno @ Elem(_,"annotation-xml",_,_,math))) =>
      assert(anno \@ "encoding" == "MathML-Content")
      println(math); fromXML(math)
    case _ => throw new RuntimeException("Invalid format: "+xml)
  }

  private def getInfo(xml:Node) : Info = {
    val id = xml \@ "id"
    val pres = xml \@ "xref"
    Info(Some(id),Some(pres))
  }
  def fromXML(xml:scala.xml.Node) : CMathML = xml match {
    case Elem(_,"apply",_,_,head,children@_*) => CApply(getInfo(xml),fromXML(head),children.map(fromXML) : _*)
    case Elem(_,"csymbol",_,_,name) => CSymbol(getInfo(xml),xml\@"cd",name.text)
    case Elem(_,"plus",_,_) => CSymbol.plus(getInfo(xml))
    case Elem(_,"ci",_,_,name) => CI(getInfo(xml),name.text)
    case _ => throw new RuntimeException("Unsupported tag "+xml.label+": "+xml)
  }
}

class CApply(info:Info, val head:CMathML, val args:List[CMathML]) extends CMathML(info) {
  override def toString : String = head+"("+args.mkString(",")+")"
}
object CApply {
  def unapplySeq(app: CApply): Some[(CMathML, Seq[CMathML])] = Some((app.head,app.args))
  def apply(info:Info, head:CMathML, args:CMathML*) = new CApply(info,head,args.toList)
}

class CSymbol(info:Info, val cd:String, val name:String) extends CMathML(info) {
  override def toString : String = cd+"."+name
}
object CSymbol {
  def apply(info:Info, cd:String, name:String) = new CSymbol(info,cd,name)
  def plus(info:Info) = CSymbol(info,"arith1","plus")
  def unapply(csymbol:CSymbol) : Some[(String,String)] = Some((csymbol.cd,csymbol.name))
  def split(cdname:String) : (String,String) = {
    val l = cdname.split('.').toList
    (l.head,l(1))
  }
}

class CI(info:Info, val name:String) extends CMathML(info) {
  override def toString : String = "$"+name
}
object CI {
  def apply(info:Info, name:String) = new CI(info,name)
  def unapply(ci:CI) : Some[String] = Some(ci.name)
}
